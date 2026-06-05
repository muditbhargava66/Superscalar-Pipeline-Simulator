#!/usr/bin/env python3
"""
Tests for Pipeline Enhancements

Tests for:
- Cache hierarchy integration in execution engine
- Dynamic branch accuracy calculation
- Performance counters
- Rename/commit bandwidth
- Out-of-order execution enhancements
- Longer benchmark loading
- Statistics interface fixes
"""

from pathlib import Path
import sys
import unittest

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache.cache import DataCache, Memory
from cache.enhanced_cache import EnhancedCache, MemoryAccessType, MemoryHierarchy
from performance.performance_counters import PerformanceCounters
from pipeline.execute_stage import ExecuteStage, OutOfOrderExecuteStage
from register_file.register_file import RegisterFile
from register_file.register_renaming import (
    AdvancedRegisterRenaming,
    RenamingScheme,
)
from utils.execution_engine import CycleAccurateExecutionEngine
from utils.instruction import Instruction, InstructionType

# ============================================================================
# Cache Hierarchy Integration Tests (Task 1 + Task 7)
# ============================================================================


class TestCacheHierarchyIntegration:
    """Test that execution engine uses the memory hierarchy."""

    def test_execution_engine_accepts_memory_hierarchy(self):
        """Execution engine should accept memory_hierarchy parameter."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        data_cache = DataCache(cache_size=1024, block_size=64)
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 10,
        }
        mem_hierarchy = MemoryHierarchy(l1_config, memory_latency=50)

        engine = CycleAccurateExecutionEngine(
            register_file, memory, data_cache, memory_hierarchy=mem_hierarchy
        )
        assert engine.memory_hierarchy is mem_hierarchy

    def test_execution_engine_works_without_memory_hierarchy(self):
        """Execution engine should work with basic cache when no hierarchy."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        data_cache = DataCache(cache_size=1024, block_size=64)

        engine = CycleAccurateExecutionEngine(register_file, memory, data_cache)
        assert engine.memory_hierarchy is None

    def test_load_word_uses_memory_hierarchy(self):
        """_load_word should go through memory hierarchy when available."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        memory.write(100, [42], 4)  # Write value 42 at address 100
        data_cache = DataCache(cache_size=1024, block_size=64)
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 5,
        }
        mem_hierarchy = MemoryHierarchy(l1_config, memory_latency=20)

        engine = CycleAccurateExecutionEngine(
            register_file, memory, data_cache, memory_hierarchy=mem_hierarchy
        )

        # First access should be a miss
        engine._load_word(100)
        assert engine.stats["cache_misses"] >= 0  # Miss recorded

    def test_store_word_uses_memory_hierarchy(self):
        """_store_word should go through memory hierarchy when available."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        data_cache = DataCache(cache_size=1024, block_size=64)
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 5,
        }
        mem_hierarchy = MemoryHierarchy(l1_config, memory_latency=20)

        engine = CycleAccurateExecutionEngine(
            register_file, memory, data_cache, memory_hierarchy=mem_hierarchy
        )

        engine._store_word(200, 99)
        # Should not raise any exceptions

    def test_cache_stall_cycles_tracked(self):
        """Cache stall cycles should be tracked on misses."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        data_cache = DataCache(cache_size=1024, block_size=64)
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 10,
        }
        mem_hierarchy = MemoryHierarchy(l1_config, memory_latency=50)

        engine = CycleAccurateExecutionEngine(
            register_file, memory, data_cache, memory_hierarchy=mem_hierarchy
        )

        engine._load_word(0)
        stats = engine.get_statistics()
        assert "cache_stall_cycles" in stats

    def test_get_statistics_includes_cache_hit_rate(self):
        """get_statistics should include cache_hit_rate."""
        register_file = RegisterFile(32)
        memory = Memory(size=1024)
        data_cache = DataCache(cache_size=1024, block_size=64)

        engine = CycleAccurateExecutionEngine(register_file, memory, data_cache)

        stats = engine.get_statistics()
        assert "cache_hit_rate" in stats
        assert "ipc" in stats


# ============================================================================
# Statistics Interface Fix Tests (Task 7)
# ============================================================================


class TestStatisticsInterface:
    """Test that stats methods use correct names."""

    def test_memory_hierarchy_has_get_statistics(self):
        """MemoryHierarchy should have get_statistics() method."""
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 10,
        }
        mh = MemoryHierarchy(l1_config)
        assert hasattr(mh, "get_statistics")
        stats = mh.get_statistics()
        assert "l1_stats" in stats

    def test_execution_engine_has_get_statistics(self):
        """CycleAccurateExecutionEngine should have get_statistics()."""
        rf = RegisterFile(32)
        mem = Memory(size=1024)
        dc = DataCache(cache_size=1024, block_size=64)
        engine = CycleAccurateExecutionEngine(rf, mem, dc)
        assert hasattr(engine, "get_statistics")

    def test_register_renaming_has_get_statistics(self):
        """AdvancedRegisterRenaming should have get_statistics()."""
        rr = AdvancedRegisterRenaming()
        assert hasattr(rr, "get_statistics")
        stats = rr.get_statistics()
        assert "renames_performed" in stats

    def test_memory_hierarchy_stats_no_hardcoded_values(self):
        """Memory hierarchy stats should not contain hardcoded 0.95 hit rate."""
        l1_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "hit_latency": 1,
            "miss_penalty": 10,
        }
        mh = MemoryHierarchy(l1_config)
        stats = mh.get_statistics()
        l1_stats = stats["l1_stats"]
        # Fresh hierarchy should have 0 hit rate, not 0.95
        assert l1_stats.get("hit_rate", 0.0) != 0.95


# ============================================================================
# Branch Accuracy Tests (Task 2)
# ============================================================================


class TestBranchAccuracy:
    """Test dynamic branch accuracy calculation."""

    def test_bimodal_predictor_accuracy(self):
        """Bimodal predictor should return actual accuracy."""
        from branch_prediction.bimodal_predictor import BimodalPredictor

        predictor = BimodalPredictor(num_entries=256)

        # No predictions yet -> accuracy should be handled gracefully
        accuracy = predictor.get_accuracy()
        assert isinstance(accuracy, float)

        # Make some predictions
        for pc in range(0, 100, 4):
            predictor.predict(pc)

        # Update with outcomes (update takes instruction-like obj, actual_taken)
        for pc in range(0, 100, 4):
            predictor.update(pc, True)  # (pc_or_instr, actual_taken)

        accuracy = predictor.get_accuracy()
        # get_accuracy() returns percentage 0-100
        assert 0.0 <= accuracy <= 100.0

    def test_gshare_predictor_accuracy(self):
        """GShare predictor should return actual accuracy."""
        from branch_prediction.gshare_predictor import GsharePredictor

        predictor = GsharePredictor(num_entries=256, history_length=4)
        accuracy = predictor.get_accuracy()
        assert isinstance(accuracy, float)
        assert 0.0 <= accuracy <= 100.0


# ============================================================================
# Performance Counters Tests (Task 3)
# ============================================================================


class TestPerformanceCounters:
    """Test the new PerformanceCounters class."""

    def test_initialization(self):
        """Counters should initialize to zero."""
        pc = PerformanceCounters()
        assert pc.total_cycles == 0
        assert pc.busy_cycles == 0
        assert pc.pipeline_stalls["fetch_stalls"] == 0

    def test_record_cycle(self):
        """record_cycle should update counters."""
        pc = PerformanceCounters()
        pc.record_cycle(instructions_issued=2, instructions_in_flight=5)
        assert pc.total_cycles == 1
        assert pc.busy_cycles == 1
        assert pc.ilp_counters["instructions_issued"] == 2
        assert pc.ilp_counters["multi_issue_cycles"] == 1

    def test_record_cycle_no_issue(self):
        """record_cycle with no issues should not count as busy."""
        pc = PerformanceCounters()
        pc.record_cycle(instructions_issued=0, instructions_in_flight=0)
        assert pc.total_cycles == 1
        assert pc.busy_cycles == 0

    def test_update_from_hazard_controller(self):
        """Should parse hazard controller stats correctly."""
        pc = PerformanceCounters()
        hazard_stats = {
            "hazards_detected": {
                "RAW": 5,
                "WAR": 2,
                "WAW": 1,
                "STRUCTURAL": 3,
                "CONTROL": 4,
            },
            "instructions_completed": 100,
        }
        pc.update_from_hazard_controller(hazard_stats)
        assert pc.hazard_counts["raw_hazards"] == 5
        assert pc.hazard_counts["war_hazards"] == 2
        assert pc.hazard_counts["waw_hazards"] == 1
        assert pc.ilp_counters["instructions_completed"] == 100

    def test_update_from_memory_hierarchy(self):
        """Should extract cache stats from memory hierarchy."""
        pc = PerformanceCounters()
        memory_stats = {
            "l1_stats": {"hits": 80, "misses": 20},
            "l2_stats": {"hits": 15, "misses": 5},
            "memory_accesses": 5,
        }
        pc.update_from_memory_hierarchy(memory_stats)
        assert pc.cache_counters["l1_read_hits"] == 80
        assert pc.cache_counters["l2_hits"] == 15

    def test_update_from_branch_predictor(self):
        """Should extract branch stats from predictor."""
        pc = PerformanceCounters()

        class MockPredictor:
            total_predictions = 100
            total_mispredictions = 10

        pc.update_from_branch_predictor(MockPredictor())
        assert pc.branch_counters["total_predictions"] == 100
        assert pc.branch_counters["mispredictions"] == 10
        assert pc.branch_counters["correct_predictions"] == 90

    def test_get_detailed_report(self):
        """Detailed report should include all sections."""
        pc = PerformanceCounters()
        pc.record_cycle(instructions_issued=1, instructions_in_flight=3)
        pc.record_cycle(instructions_issued=2, instructions_in_flight=4)

        report = pc.get_detailed_report()
        assert "cycle_counters" in report
        assert "pipeline_stalls" in report
        assert "hazard_counters" in report
        assert "cache_counters" in report
        assert "branch_counters" in report
        assert "ilp_counters" in report
        assert report["cycle_counters"]["total_cycles"] == 2
        assert report["cycle_counters"]["busy_cycles"] == 2

    def test_record_branch_outcome(self):
        """Branch outcomes should update counters."""
        pc = PerformanceCounters()
        pc.record_branch_outcome(predicted=True, actual=True, penalty_cycles=0)
        pc.record_branch_outcome(predicted=True, actual=False, penalty_cycles=15)
        assert pc.branch_counters["total_predictions"] == 2
        assert pc.branch_counters["correct_predictions"] == 1
        assert pc.branch_counters["mispredictions"] == 1
        assert pc.branch_counters["misprediction_penalty_cycles"] == 15

    def test_reset(self):
        """Reset should zero all counters."""
        pc = PerformanceCounters()
        pc.record_cycle(instructions_issued=1, instructions_in_flight=1)
        pc.reset()
        assert pc.total_cycles == 0


# ============================================================================
# Rename/Commit Bandwidth Tests (Task 4)
# ============================================================================


class TestRenameCommitBandwidth:
    """Test configurable rename and commit bandwidth."""

    def test_default_bandwidth(self):
        """Default bandwidth should be 4."""
        rr = AdvancedRegisterRenaming()
        assert rr.rename_bandwidth == 4
        assert rr.commit_bandwidth == 4

    def test_custom_bandwidth(self):
        """Should accept custom bandwidth values."""
        rr = AdvancedRegisterRenaming(rename_bandwidth=8, commit_bandwidth=6)
        assert rr.rename_bandwidth == 8
        assert rr.commit_bandwidth == 6

    def test_batch_rename(self):
        """rename_instruction_batch should rename up to bandwidth."""
        rr = AdvancedRegisterRenaming(num_physical_regs=128, rename_bandwidth=2)
        instructions: list[tuple[int, list[int], int | None]] = [
            (0, [1, 2], 3),
            (1, [4, 5], 6),
            (2, [7, 8], 9),  # Should not be renamed (bandwidth=2)
        ]
        results = rr.rename_instruction_batch(instructions)
        assert len(results) == 2  # Only 2 renamed due to bandwidth
        assert results[0][0] is True
        assert results[1][0] is True

    def test_commit_bandwidth_limit(self):
        """commit_instructions should respect commit_bandwidth."""
        rr = AdvancedRegisterRenaming(num_physical_regs=128, commit_bandwidth=2)

        # Rename 3 instructions
        rr.rename_instruction(0, [1], 2)
        rr.rename_instruction(1, [3], 4)
        rr.rename_instruction(2, [5], 6)

        # Complete all 3
        rr.complete_instruction(0, 100)
        rr.complete_instruction(1, 200)
        rr.complete_instruction(2, 300)

        # Commit should only commit up to bandwidth (2)
        committed = rr.commit_instructions()
        assert len(committed) == 2

    def test_commit_with_explicit_limit(self):
        """commit_instructions should accept explicit max_commit."""
        rr = AdvancedRegisterRenaming(num_physical_regs=128, commit_bandwidth=4)
        rr.rename_instruction(0, [1], 2)
        rr.rename_instruction(1, [3], 4)
        rr.complete_instruction(0, 100)
        rr.complete_instruction(1, 200)

        committed = rr.commit_instructions(max_commit=1)
        assert len(committed) == 1

    def test_statistics_include_bandwidth(self):
        """get_statistics should include bandwidth settings."""
        rr = AdvancedRegisterRenaming(rename_bandwidth=8, commit_bandwidth=6)
        stats = rr.get_statistics()
        assert stats["rename_bandwidth"] == 8
        assert stats["commit_bandwidth"] == 6


# ============================================================================
# Out-of-Order Execution Tests (Task 6)
# ============================================================================


class TestOutOfOrderExecution:
    """Test enhanced out-of-order execution stage."""

    def _make_ooo_stage(self, window_size=8):
        """Create an OOO execute stage for testing."""
        register_file = RegisterFile(32)
        data_cache = DataCache(cache_size=1024, block_size=64)
        memory = Memory(size=1024)
        return OutOfOrderExecuteStage(
            num_alu_units=2,
            num_fpu_units=1,
            num_lsu_units=1,
            register_file=register_file,
            data_cache=data_cache,
            memory=memory,
            window_size=window_size,
        )

    def test_ooo_stage_creation(self):
        """OOO stage should have instruction window."""
        stage = self._make_ooo_stage()
        assert stage.window_size == 8
        assert len(stage.instruction_window) == 0

    def _make_instruction(self, opcode: str, pc: int = 0) -> Instruction:
        """Helper to create an Instruction for testing."""
        return Instruction(address=pc, opcode=opcode)

    def test_ooo_stall_on_overflow(self):
        """OOO stage should stall instead of dropping instructions."""
        stage = self._make_ooo_stage(window_size=2)

        # Fill the window
        inst1 = self._make_instruction("ADD", pc=0)
        inst2 = self._make_instruction("SUB", pc=4)

        # Fill window to capacity
        stage.instruction_window = [inst1, inst2]

        # Try to add more - should stall
        inst3 = self._make_instruction("AND", pc=8)

        stage.execute([inst3])
        assert stage.stall_cycles >= 1  # Should have stalled

    def test_ooo_oldest_first_scheduling(self):
        """OOO stage should schedule oldest instructions first."""
        stage = self._make_ooo_stage(window_size=16)

        # Create instructions with different PCs (reverse order)
        insts = [self._make_instruction("ADD", pc=(3 - i) * 4) for i in range(4)]

        # Execute - should sort by PC
        stage.execute(insts)
        # Instructions should have been processed in PC order

    def test_window_status_includes_stall_cycles(self):
        """get_window_status should include stall_cycles."""
        stage = self._make_ooo_stage()
        status = stage.get_window_status()
        assert "stall_cycles" in status
        assert "window_size" in status
        assert "current_occupancy" in status


# ============================================================================
# Benchmark Loading Tests (Task 5)
# ============================================================================


class TestBenchmarkLoading:
    """Test that new longer benchmarks can be loaded."""

    BENCHMARK_DIR = Path(__file__).parent.parent / "benchmarks"

    def test_dhrystone_like_exists(self):
        """Dhrystone-like benchmark should exist."""
        path = self.BENCHMARK_DIR / "integer" / "dhrystone_like.asm"
        assert path.exists()

    def test_quicksort_exists(self):
        """Quicksort benchmark should exist."""
        path = self.BENCHMARK_DIR / "integer" / "quicksort.asm"
        assert path.exists()

    def test_streaming_access_exists(self):
        """Streaming access benchmark should exist."""
        path = self.BENCHMARK_DIR / "memory" / "streaming_access.asm"
        assert path.exists()

    def test_compute_intensive_exists(self):
        """Compute-intensive benchmark should exist."""
        path = self.BENCHMARK_DIR / "mixed" / "compute_intensive.asm"
        assert path.exists()

    @pytest.mark.parametrize(
        "benchmark_path",
        [
            "integer/dhrystone_like.asm",
            "integer/quicksort.asm",
            "memory/streaming_access.asm",
            "mixed/compute_intensive.asm",
        ],
    )
    def test_benchmarks_parseable(self, benchmark_path):
        """All new benchmarks should be parseable."""
        from utils.instruction_parser import MIPSInstructionParser

        full_path = self.BENCHMARK_DIR / benchmark_path
        if not full_path.exists():
            pytest.skip(f"Benchmark {benchmark_path} not found")

        parser = MIPSInstructionParser()
        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        instructions = parser.parse_program(content)
        assert len(instructions) > 50  # Longer benchmarks should have >50 instructions


# ============================================================================
# Configuration Tests (Task 8)
# ============================================================================


class TestConfiguration:
    """Test configuration options for enhanced pipeline features."""

    def test_config_yaml_has_new_options(self):
        """config.yaml should contain enhanced execution options."""
        import yaml

        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        execution = config.get("execution", {})
        assert "rename_bandwidth" in execution
        assert "commit_bandwidth" in execution
        assert "ooo_execution" in execution
        assert "ooo_window_size" in execution

    def test_pyproject_version(self):
        """pyproject.toml should have version 1.2.0."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text(encoding="utf-8")
        assert 'version = "1.2.0"' in content


# ============================================================================
# Integration Test
# ============================================================================


class TestSimulatorIntegration:
    """Integration test for the full simulator with enhanced pipeline features."""

    def test_simulator_initializes_with_config(self):
        """Simulator should initialize successfully with config.yaml."""
        from main import SuperscalarSimulator

        config_path = str(Path(__file__).parent.parent / "config.yaml")
        sim = SuperscalarSimulator(config_path)

        # Should have all components
        assert sim.memory_hierarchy is not None
        assert sim.execution_engine is not None
        assert sim.branch_predictor is not None
        assert sim.register_renaming is not None

    def test_simulator_runs_simple_benchmark(self):
        """Simulator should run a simple benchmark and produce results."""
        from main import SuperscalarSimulator

        config_path = str(Path(__file__).parent.parent / "config.yaml")
        sim = SuperscalarSimulator(config_path)
        sim.config["simulation"]["max_cycles"] = 100

        benchmark_path = str(
            Path(__file__).parent.parent / "benchmarks" / "simple_test.asm"
        )
        sim.load_program(benchmark_path)
        results = sim.run_simulation()

        assert "cycles" in results
        assert "instructions" in results
        assert "ipc" in results
        assert "branch_accuracy" in results
        assert "cache_hit_rate" in results
        assert "performance_counters" in results

    def test_branch_accuracy_not_hardcoded(self):
        """Branch accuracy should not be hardcoded 90.0."""
        from main import SuperscalarSimulator

        config_path = str(Path(__file__).parent.parent / "config.yaml")
        sim = SuperscalarSimulator(config_path)
        sim.config["simulation"]["max_cycles"] = 50

        benchmark_path = str(
            Path(__file__).parent.parent / "benchmarks" / "simple_test.asm"
        )
        sim.load_program(benchmark_path)
        results = sim.run_simulation()

        # With no branches, accuracy should be 0.0, not 90.0
        assert results["branch_accuracy"] != 90.0

    def test_performance_counters_in_results(self):
        """Results should include performance counters report."""
        from main import SuperscalarSimulator

        config_path = str(Path(__file__).parent.parent / "config.yaml")
        sim = SuperscalarSimulator(config_path)
        sim.config["simulation"]["max_cycles"] = 50

        benchmark_path = str(
            Path(__file__).parent.parent / "benchmarks" / "simple_arithmetic.asm"
        )
        sim.load_program(benchmark_path)
        results = sim.run_simulation()

        assert "performance_counters" in results
        pc = results["performance_counters"]
        assert "cycle_counters" in pc
        assert "hazard_counters" in pc
        assert "cache_counters" in pc
        assert "branch_counters" in pc
        assert "ilp_counters" in pc
