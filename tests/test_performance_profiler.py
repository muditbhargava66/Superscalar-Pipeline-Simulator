#!/usr/bin/env python3
"""
Test suite for the Performance Profiler and Optimizer.

Validates PerformanceProfiler cycle tracking, instruction mix classification,
branch / cache / stall / hazard recording, bottleneck identification, critical
path analysis, report generation, and PerformanceOptimizer suggestions.
"""

import json
from pathlib import Path
import tempfile

import pytest

from src.performance.profiler import (
    CycleSnapshot,
    PerformanceMetrics,
    PerformanceOptimizer,
    PerformanceProfiler,
)

# ============================== Fixtures ====================================


@pytest.fixture
def profiler() -> PerformanceProfiler:
    """Profiler with detailed tracking enabled."""
    return PerformanceProfiler(enable_detailed_tracking=True)


@pytest.fixture
def basic_profiler() -> PerformanceProfiler:
    """Profiler without detailed tracking (lightweight mode)."""
    return PerformanceProfiler(enable_detailed_tracking=False)


@pytest.fixture
def optimizer(profiler: PerformanceProfiler) -> PerformanceOptimizer:
    return PerformanceOptimizer(profiler)


# ==================== PerformanceMetrics dataclass ==========================


class TestPerformanceMetrics:
    """Verify the raw metric container and derived-metric calculation."""

    def test_default_values(self) -> None:
        m = PerformanceMetrics()
        assert m.total_cycles == 0
        assert m.total_instructions == 0
        assert m.ipc == 0.0
        assert m.branch_accuracy == 0.0

    def test_calculate_derived_ipc(self) -> None:
        m = PerformanceMetrics()
        m.total_cycles = 100
        m.total_instructions = 250
        m.calculate_derived_metrics()
        assert m.ipc == pytest.approx(2.5)

    def test_calculate_branch_accuracy(self) -> None:
        m = PerformanceMetrics()
        m.branch_predictions = 100
        m.branch_mispredictions = 10
        m.calculate_derived_metrics()
        assert m.branch_accuracy == pytest.approx(90.0)

    def test_cache_hit_rates(self) -> None:
        m = PerformanceMetrics()
        m.icache_hits = 90
        m.icache_misses = 10
        m.dcache_hits = 80
        m.dcache_misses = 20
        m.calculate_derived_metrics()
        assert m.icache_hit_rate == pytest.approx(90.0)
        assert m.dcache_hit_rate == pytest.approx(80.0)

    def test_total_stalls_aggregation(self) -> None:
        m = PerformanceMetrics()
        m.data_stalls = 5
        m.structural_stalls = 3
        m.control_stalls = 2
        m.calculate_derived_metrics()
        assert m.total_stalls == 10


# ==================== PerformanceProfiler core ==============================


class TestProfilerCycleTracking:
    """Cycle-level tracking: start/end cycle and snapshot creation."""

    def test_start_cycle_creates_snapshot(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        assert len(profiler.cycle_snapshots) == 1
        assert profiler.cycle_snapshots[0].cycle == 1

    def test_end_cycle_increments_total(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.end_cycle()
        assert profiler.metrics.total_cycles == 1

    def test_ipc_history_updated(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.record_instruction_complete("ADD $1, $2, $3", 1, 3)
        profiler.end_cycle()
        assert len(profiler.ipc_history) == 1

    def test_lightweight_mode_no_snapshots(
        self, basic_profiler: PerformanceProfiler
    ) -> None:
        basic_profiler.start_cycle(1)
        assert len(basic_profiler.cycle_snapshots) == 0


# ==================== Instruction Tracking ==================================


class TestInstructionTracking:
    """Instruction completion recording and mix classification."""

    def test_record_instruction_complete(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete(
            "ADD $1, $2, $3", issue_cycle=1, complete_cycle=5
        )
        assert profiler.metrics.total_instructions == 1
        assert profiler.instruction_counts["ADD $1, $2, $3"] == 1

    def test_latency_recorded(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("LW $4, 0($5)", 2, 10)
        latencies = profiler.instruction_latencies["LW $4, 0($5)"]
        assert latencies == [8]

    def test_arithmetic_classification(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("ADD $1, $2, $3", 1, 2)
        profiler.record_instruction_complete("SUB $4, $5, $6", 1, 2)
        assert profiler.metrics.arithmetic_instructions == 2

    def test_logical_classification(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("AND $1, $2, $3", 1, 2)
        profiler.record_instruction_complete("XOR $4, $5, $6", 1, 2)
        assert profiler.metrics.logical_instructions == 2

    def test_memory_classification(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("LW $1, 0($2)", 1, 3)
        profiler.record_instruction_complete("SW $3, 4($4)", 1, 3)
        assert profiler.metrics.memory_instructions == 2

    def test_branch_classification(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("BEQ $1, $2, label", 1, 2)
        assert profiler.metrics.branch_instructions == 1

    def test_float_classification(self, profiler: PerformanceProfiler) -> None:
        profiler.record_instruction_complete("FADD $f1, $f2, $f3", 1, 5)
        assert profiler.metrics.floating_point_instructions == 1

    def test_record_instruction_fetch(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.record_instruction_fetch(["ADD $1, $2, $3", "SUB $4, $5, $6"])
        assert len(profiler.cycle_snapshots[-1].fetched_instructions) == 2


# ==================== Branch Prediction =====================================


class TestBranchPrediction:
    """Branch prediction recording and accuracy tracking."""

    def test_correct_prediction(self, profiler: PerformanceProfiler) -> None:
        profiler.record_branch_prediction("BEQ $1, $2, L1", predicted=True, actual=True)
        assert profiler.metrics.branch_predictions == 1
        assert profiler.metrics.branch_mispredictions == 0

    def test_misprediction_penalty(self, profiler: PerformanceProfiler) -> None:
        profiler.record_branch_prediction(
            "BNE $1, $2, L2", predicted=True, actual=False
        )
        assert profiler.metrics.branch_mispredictions == 1
        assert profiler.metrics.branch_penalty_cycles == 3

    def test_accuracy_history(self, profiler: PerformanceProfiler) -> None:
        profiler.record_branch_prediction("BEQ", True, True)
        profiler.record_branch_prediction("BNE", True, False)
        assert len(profiler.branch_accuracy_history) == 2


# ==================== Cache Access ==========================================


class TestCacheAccess:
    """Cache hit/miss recording for instruction and data caches."""

    def test_icache_hit(self, profiler: PerformanceProfiler) -> None:
        profiler.record_cache_access("instruction", hit=True)
        assert profiler.metrics.icache_hits == 1

    def test_icache_miss_penalty(self, profiler: PerformanceProfiler) -> None:
        profiler.record_cache_access("instruction", hit=False, miss_penalty=15)
        assert profiler.metrics.icache_misses == 1
        assert profiler.metrics.cache_miss_penalty_cycles == 15

    def test_dcache_hit(self, profiler: PerformanceProfiler) -> None:
        profiler.record_cache_access("data", hit=True)
        assert profiler.metrics.dcache_hits == 1

    def test_dcache_miss(self, profiler: PerformanceProfiler) -> None:
        profiler.record_cache_access("data", hit=False, miss_penalty=20)
        assert profiler.metrics.dcache_misses == 1
        assert profiler.metrics.cache_miss_penalty_cycles == 20


# ==================== Stalls and Hazards ====================================


class TestStallsAndHazards:
    """Stall and hazard recording and classification."""

    def test_data_stall(self, profiler: PerformanceProfiler) -> None:
        profiler.record_stall("data", duration=3)
        assert profiler.metrics.data_stalls == 3

    def test_structural_stall(self, profiler: PerformanceProfiler) -> None:
        profiler.record_stall("structural", duration=2)
        assert profiler.metrics.structural_stalls == 2

    def test_control_stall(self, profiler: PerformanceProfiler) -> None:
        profiler.record_stall("control", duration=5)
        assert profiler.metrics.control_stalls == 5

    def test_raw_hazard(self, profiler: PerformanceProfiler) -> None:
        profiler.record_hazard("RAW", "Register $5 dependency")
        assert profiler.metrics.raw_hazards == 1

    def test_war_hazard(self, profiler: PerformanceProfiler) -> None:
        profiler.record_hazard("WAR", "Register $3 anti-dependency")
        assert profiler.metrics.war_hazards == 1

    def test_waw_hazard(self, profiler: PerformanceProfiler) -> None:
        profiler.record_hazard("WAW", "Register $7 output-dependency")
        assert profiler.metrics.waw_hazards == 1


# ==================== Functional Unit Utilization ============================


class TestFunctionalUnitUtilization:
    """Track ALU/FPU/LSU utilization percentages."""

    def test_alu_utilization(self, profiler: PerformanceProfiler) -> None:
        profiler.record_functional_unit_usage("ALU", busy_cycles=60, total_cycles=100)
        assert profiler.metrics.alu_utilization == pytest.approx(60.0)

    def test_fpu_utilization(self, profiler: PerformanceProfiler) -> None:
        profiler.record_functional_unit_usage("FPU", busy_cycles=30, total_cycles=100)
        assert profiler.metrics.fpu_utilization == pytest.approx(30.0)

    def test_lsu_utilization(self, profiler: PerformanceProfiler) -> None:
        profiler.record_functional_unit_usage("LSU", busy_cycles=45, total_cycles=100)
        assert profiler.metrics.lsu_utilization == pytest.approx(45.0)

    def test_zero_total_cycles_ignored(self, profiler: PerformanceProfiler) -> None:
        profiler.record_functional_unit_usage("ALU", busy_cycles=0, total_cycles=0)
        assert profiler.metrics.alu_utilization == 0.0


# ==================== Bottleneck & Critical Path ============================


class TestBottleneckAnalysis:
    """Bottleneck identification and critical-path analysis."""

    def test_identify_bottleneck(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(10)
        profiler.identify_bottleneck("Cache thrashing", severity="high")
        assert len(profiler.bottleneck_events) == 1
        assert profiler.bottleneck_events[0]["severity"] == "high"

    def test_critical_path_empty_initially(self, profiler: PerformanceProfiler) -> None:
        path = profiler.analyze_critical_path()
        assert path == []

    def test_critical_path_high_latency(self, profiler: PerformanceProfiler) -> None:
        # Record instruction with latency > 10 (threshold for critical)
        for _ in range(3):
            profiler.record_instruction_complete("LDIV $f1, $f2, $f3", 1, 20)
        path = profiler.analyze_critical_path()
        assert "LDIV $f1, $f2, $f3" in path


# ==================== Report Generation =====================================


class TestReportGeneration:
    """Performance summary and recommendation generation."""

    def test_get_performance_summary(self, profiler: PerformanceProfiler) -> None:
        # Run a few cycles with various events
        for c in range(1, 11):
            profiler.start_cycle(c)
            profiler.record_instruction_complete("ADD $1, $2, $3", c, c + 1)
            profiler.record_cache_access("instruction", hit=True)
            profiler.end_cycle()

        summary = profiler.get_performance_summary()
        assert "basic_metrics" in summary
        assert summary["basic_metrics"]["total_cycles"] == 10
        assert summary["basic_metrics"]["total_instructions"] == 10
        assert "branch_performance" in summary
        assert "cache_performance" in summary
        assert "stall_analysis" in summary
        assert "instruction_mix" in summary

    def test_recommendations_low_ipc(self, profiler: PerformanceProfiler) -> None:
        # Simulate low IPC scenario
        for c in range(1, 101):
            profiler.start_cycle(c)
            profiler.end_cycle()
        # 100 cycles, only 1 instruction → IPC = 0.01
        profiler.record_instruction_complete("NOP", 1, 2)
        recs = profiler.generate_recommendations()
        # Should recommend improving IPC
        assert any("IPC" in r for r in recs)

    def test_export_json_report(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.record_instruction_complete("ADD $1, $2, $3", 1, 2)
        profiler.end_cycle()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmppath = Path(f.name)

        profiler.export_report(tmppath, format="json")
        data = json.loads(tmppath.read_text())
        assert "summary" in data
        assert "recommendations" in data
        tmppath.unlink()

    def test_export_csv_report(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.end_cycle()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            tmppath = Path(f.name)

        profiler.export_report(tmppath, format="csv")
        content = tmppath.read_text()
        assert "Metric" in content
        tmppath.unlink()

    def test_export_txt_report(self, profiler: PerformanceProfiler) -> None:
        profiler.start_cycle(1)
        profiler.end_cycle()

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            tmppath = Path(f.name)

        profiler.export_report(tmppath, format="txt")
        content = tmppath.read_text()
        assert "SUPERSCALAR PIPELINE PERFORMANCE REPORT" in content
        tmppath.unlink()


# ==================== PerformanceOptimizer ==================================


class TestPerformanceOptimizer:
    """Optimizer branch-pattern analysis and compiler optimization hints."""

    def test_instantiation(self, optimizer: PerformanceOptimizer) -> None:
        assert optimizer.profiler is not None

    def test_analyze_branch_patterns(self, optimizer: PerformanceOptimizer) -> None:
        patterns = optimizer.analyze_branch_patterns()
        assert "always_taken" in patterns
        assert "random" in patterns

    def test_suggest_compiler_optimizations(
        self, optimizer: PerformanceOptimizer
    ) -> None:
        suggestions = optimizer.suggest_compiler_optimizations()
        assert isinstance(suggestions, list)
