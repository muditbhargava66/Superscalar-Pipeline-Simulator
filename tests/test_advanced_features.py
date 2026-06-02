#!/usr/bin/env python3
"""
Comprehensive Tests for Advanced Simulator Features

This module tests all advanced features of the Superscalar Pipeline Simulator:
- Configuration management and validation
- Error handling system
- Performance and memory profiling
- Hybrid branch predictors (Tournament, Perceptron, Adaptive)
- Non-blocking cache with MSHR support
- Enhanced register renaming with deep ROB
- Power and energy modeling
"""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configuration and error handling
# Advanced branch prediction
from branch_prediction.hybrid_predictor import (
    AdaptiveHybridPredictor,
    PerceptronPredictor,
    TournamentPredictor,
)

# Cache hierarchy
from cache.non_blocking_cache import MSHR, MSHRState, NonBlockingCache
from config import ConfigManager, PipelineConfig, SimulatorConfig
from exceptions import (
    ConfigurationError,
    MemoryAccessError,
    PipelineError,
    handle_simulator_error,
)

# Profiling
from profiling import MemoryProfiler, PerformanceProfiler

# Power modeling
from profiling.power_model import (
    ComponentPowerModel,
    PowerParameters,
    ProcessorPowerModel,
)

# Register renaming
from register_file.enhanced_register_renaming import EnhancedRegisterRenaming

# Instructions
from utils.instruction import Instruction, InstructionType

# ============================================================================
# Configuration Management Tests
# ============================================================================


class TestConfigurationManagement(unittest.TestCase):
    """Test the configuration management system."""

    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        for file in self.temp_dir.glob("*"):
            file.unlink()
        self.temp_dir.rmdir()

    def test_default_configuration_loading(self):
        """Test loading default configuration."""
        config = self.config_manager.load_default()

        self.assertIsInstance(config, SimulatorConfig)
        self.assertEqual(config.pipeline.num_stages, 6)
        self.assertEqual(config.pipeline.fetch_width, 4)
        self.assertEqual(config.branch_predictor.type.value, "gshare")

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration
        valid_config = {
            "pipeline": {
                "num_stages": 5,
                "fetch_width": 4,
                "issue_width": 4,
            }
        }

        config = self.config_manager.create_from_dict(valid_config)
        self.assertEqual(config.pipeline.num_stages, 5)

        # Invalid configuration
        invalid_config = {
            "pipeline": {
                "num_stages": 15,  # Too many stages
                "fetch_width": 0,  # Too small
            }
        }

        with self.assertRaises(ConfigurationError):
            self.config_manager.create_from_dict(invalid_config)

    def test_environment_variable_overrides(self):
        """Test environment variable configuration overrides."""
        os.environ["SIMULATOR_PIPELINE__FETCH_WIDTH"] = "8"
        os.environ["SIMULATOR_DEBUG__ENABLED"] = "true"

        try:
            config = self.config_manager.load_default()

            self.assertEqual(config.pipeline.fetch_width, 8)
            self.assertTrue(config.debug.enabled)
        finally:
            os.environ.pop("SIMULATOR_PIPELINE__FETCH_WIDTH", None)
            os.environ.pop("SIMULATOR_DEBUG__ENABLED", None)

    def test_configuration_file_operations(self):
        """Test configuration file loading and saving."""
        config = self.config_manager.load_default()
        config.pipeline.fetch_width = 6

        # Save to file
        config_file = self.temp_dir / "test_config.yaml"
        config.save_to_file(config_file)

        self.assertTrue(config_file.exists())

        # Load from file
        loaded_config = self.config_manager.load_from_file(config_file)
        self.assertEqual(loaded_config.pipeline.fetch_width, 6)

    def test_configuration_validation_utility(self):
        """Test configuration file validation utility."""
        config = self.config_manager.load_default()
        valid_config_file = self.temp_dir / "valid_config.yaml"
        config.save_to_file(valid_config_file)

        # Validate valid config
        is_valid, errors = self.config_manager.validate_config_file(valid_config_file)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Validate invalid config
        invalid_config_file = self.temp_dir / "invalid_config.yaml"
        with open(invalid_config_file, "w") as f:
            f.write("pipeline:\n  num_stages: 15\n  fetch_width: 0\n")

        is_valid, errors = self.config_manager.validate_config_file(invalid_config_file)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling(unittest.TestCase):
    """Test the error handling system."""

    def test_simulator_error_hierarchy(self):
        """Test the exception hierarchy."""
        base_error = ConfigurationError("Test error", details={"key": "value"})
        self.assertEqual(base_error.message, "Test error")
        self.assertEqual(base_error.details["key"], "value")

        self.assertIsInstance(base_error, ConfigurationError)

        error_str = str(base_error)
        self.assertIn("Test error", error_str)
        self.assertIn("key=value", error_str)

    def test_pipeline_error_context(self):
        """Test pipeline error with context."""
        error = PipelineError(
            "Test pipeline error",
            stage="execute",
            cycle=100,
            instruction="ADD $t0, $t1, $t2",
        )

        self.assertEqual(error.stage, "execute")
        self.assertEqual(error.cycle, 100)
        self.assertEqual(error.details["stage"], "execute")
        self.assertEqual(error.details["cycle"], 100)

    def test_memory_access_error(self):
        """Test memory access error."""
        error = MemoryAccessError(
            "Out of bounds access", address=0x10000, access_type="read"
        )

        self.assertEqual(error.address, 0x10000)
        self.assertEqual(error.access_type, "read")
        self.assertEqual(error.details["address"], "0x10000")
        self.assertEqual(error.details["access_type"], "read")

    def test_error_handling_utility(self):
        """Test error handling utility function."""
        error = PipelineError("Test error", stage="decode", cycle=50)

        mock_logger = MagicMock()
        error_info = handle_simulator_error(error, mock_logger)

        self.assertEqual(error_info["type"], "PipelineError")
        self.assertEqual(error_info["message"], "Test error")
        self.assertEqual(error_info["details"]["stage"], "decode")

        mock_logger.error.assert_called_once()


# ============================================================================
# Performance Profiling Tests
# ============================================================================


class TestPerformanceProfiling(unittest.TestCase):
    """Test the performance profiling system."""

    def test_performance_profiler_basic(self):
        """Test basic performance profiler functionality."""
        profiler = PerformanceProfiler(enable_detailed_profiling=False)

        with profiler.profile_simulation() as session:
            sum(i * i for i in range(1000))

        result = session.get_results()

        self.assertIsNotNone(result)
        self.assertGreater(result.execution_time, 0)
        self.assertIsInstance(result.cpu_usage, dict)
        self.assertIsInstance(result.memory_usage, dict)

    def test_performance_profiler_detailed(self):
        """Test detailed performance profiling."""
        profiler = PerformanceProfiler(enable_detailed_profiling=True)

        profiler.start_profiling()

        def test_function():
            return sum(i for i in range(1000))

        test_function()

        profile_result = profiler.stop_profiling()

        self.assertIsNotNone(profile_result)
        self.assertGreater(profile_result.execution_time, 0)
        self.assertIsInstance(profile_result.function_stats, dict)

    def test_bottleneck_analyzer(self):
        """Test bottleneck analysis."""
        profiler = PerformanceProfiler()

        with profiler.profile_simulation() as session:
            total = 0
            for i in range(10000):
                total += i * i

        result = session.get_results()

        self.assertIsInstance(result.bottlenecks, list)
        self.assertIsInstance(result.recommendations, list)


# ============================================================================
# Memory Profiling Tests
# ============================================================================


class TestMemoryProfiling(unittest.TestCase):
    """Test the memory profiling system."""

    def test_memory_profiler_basic(self):
        """Test basic memory profiler functionality."""
        profiler = MemoryProfiler(track_allocations=False)

        profiler.start_profiling()

        [list(range(100)) for _ in range(100)]

        result = profiler.stop_profiling()

        self.assertIsNotNone(result)
        self.assertIsInstance(result.memory_growth, float)
        self.assertGreater(result.peak_memory, 0)

    def test_memory_profiler_with_tracking(self):
        """Test memory profiler with allocation tracking."""
        profiler = MemoryProfiler(track_allocations=True)

        profiler.start_profiling()
        profiler.take_snapshot()

        [list(range(1000)) for _ in range(100)]

        profiler.take_snapshot()

        result = profiler.stop_profiling()

        self.assertIsNotNone(result)
        self.assertIsInstance(result.memory_growth, float)
        self.assertGreaterEqual(len(result.potential_leaks), 0)
        self.assertIsInstance(result.recommendations, list)


# ============================================================================
# Hybrid Branch Prediction Tests
# ============================================================================


class TestHybridBranchPredictors:
    """Test hybrid branch prediction algorithms."""

    def test_tournament_predictor_basic(self):
        """Test basic tournament predictor functionality."""
        config = {
            "predictor_1": {"size": 64},
            "predictor_2": {"size": 64, "history_bits": 6},
            "meta_bits": 6,
        }
        predictor = TournamentPredictor(config)

        result = predictor.predict(0x1000)
        assert result.taken in [True, False]
        assert 0.0 <= result.confidence <= 1.0
        assert "predictor_used" in result.metadata

        predictor.update(0x1000, True)
        stats = predictor.get_stats()
        assert stats["predictions"] == 1
        assert stats["predictor_type"] == "tournament"

    def test_perceptron_predictor_basic(self):
        """Test basic perceptron predictor functionality."""
        config = {"history_length": 8, "table_size": 64, "theta": 20}
        predictor = PerceptronPredictor(config)

        result = predictor.predict(0x1000)
        assert result.taken in [True, False]
        assert 0.0 <= result.confidence <= 1.0
        assert "output" in result.metadata
        assert "theta" in result.metadata

        for i in range(10):
            pc = 0x1000 + i * 4
            taken = i % 2 == 0
            predictor.update(pc, taken)

        stats = predictor.get_stats()
        assert stats["predictions"] == 10
        assert stats["predictor_type"] == "perceptron"

    def test_adaptive_hybrid_predictor(self):
        """Test adaptive hybrid predictor switching."""
        config = {
            "tournament": {
                "predictor_1": {"size": 32},
                "predictor_2": {"size": 32, "history_bits": 4},
                "meta_bits": 4,
            },
            "perceptron": {"history_length": 6, "table_size": 32, "theta": 15},
            "adaptation_window": 20,
            "adaptation_threshold": 0.1,
        }
        predictor = AdaptiveHybridPredictor(config)

        result = predictor.predict(0x1000)
        assert "active_predictor" in result.metadata

        for i in range(25):
            pc = 0x1000 + i * 4
            taken = i % 3 == 0
            predictor.update(pc, taken)

        stats = predictor.get_stats()
        assert stats["predictions"] == 25
        assert stats["predictor_type"] == "adaptive_hybrid"
        assert "tournament_stats" in stats
        assert "perceptron_stats" in stats


# ============================================================================
# Non-Blocking Cache Tests
# ============================================================================


class TestNonBlockingCache:
    """Test non-blocking cache with MSHR support."""

    def test_non_blocking_cache_creation(self):
        """Test non-blocking cache initialization."""
        config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "mshr_count": 4,
            "hit_latency": 1,
            "miss_penalty": 10,
        }
        cache = NonBlockingCache(config)

        assert cache.cache_size == 1024
        assert cache.mshr_count == 4
        assert len(cache.mshrs) == 0

    def test_mshr_allocation(self):
        """Test MSHR allocation on cache miss."""
        config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "mshr_count": 4,
        }
        cache = NonBlockingCache(config)

        data, hit = cache.read(0x1000, instruction_id=1)
        assert not hit
        assert data is None
        assert len(cache.mshrs) == 1

        data2, hit2 = cache.read(0x1000, instruction_id=2)
        assert not hit2
        assert len(cache.mshrs) == 1

        block_addr = cache._get_block_address(0x1000)
        mshr = cache.mshrs[block_addr]
        assert mshr.state == MSHRState.ALLOCATED
        assert len(mshr.pending_loads) == 2

    def test_speculative_load_support(self):
        """Test speculative load tracking and squashing."""
        config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "mshr_count": 4,
        }
        cache = NonBlockingCache(config)

        cache.add_speculative_load(0x2000, 0x1000, instruction_id=1)
        assert 0x2000 in cache.speculative_loads

        cache.handle_branch_misprediction(0x2000)
        assert 0x2000 not in cache.speculative_loads

    def test_cache_advance_cycle(self):
        """Test cache cycle advancement and MSHR processing."""
        config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "mshr_count": 4,
            "miss_penalty": 3,
        }
        cache = NonBlockingCache(config)

        cache.read(0x1000, instruction_id=1)
        block_addr = cache._get_block_address(0x1000)

        for cycle in range(5):
            cache.advance_cycle()

        assert block_addr not in cache.mshrs


# ============================================================================
# Enhanced Register Renaming Tests
# ============================================================================


class TestEnhancedRegisterRenaming:
    """Test enhanced register renaming with deep ROB."""

    def test_register_renaming_creation(self):
        """Test enhanced register renaming initialization."""
        config = {
            "arch_registers": 32,
            "physical_registers": 64,
            "rob_size": 32,
            "issue_queue_size": 16,
        }
        renaming = EnhancedRegisterRenaming(config)

        assert renaming.arch_registers == 32
        assert renaming.physical_registers == 64
        assert renaming.rob_size == 32
        assert len(renaming.free_list) == 32

    def test_instruction_renaming(self):
        """Test instruction register renaming."""
        config = {
            "arch_registers": 32,
            "physical_registers": 64,
            "rob_size": 32,
            "issue_queue_size": 16,
        }
        renaming = EnhancedRegisterRenaming(config)

        instruction = Instruction(
            address=0x1000,
            opcode="add",
            operands=["$t0", "$t1", "$t2"],
            destination="$t0",
            instruction_type=InstructionType.ARITHMETIC,
        )

        rob_id = renaming.rename_instruction(instruction)
        assert rob_id is not None
        assert rob_id == 0
        assert renaming.rob_count == 1

        assert renaming.rat[8] != 8

    def test_instruction_issue(self):
        """Test instruction issuing from issue queue."""
        config = {
            "arch_registers": 32,
            "physical_registers": 64,
            "rob_size": 32,
            "issue_queue_size": 16,
            "alu_count": 2,
        }
        renaming = EnhancedRegisterRenaming(config)

        instruction = Instruction(
            address=0x1000,
            opcode="add",
            operands=["$t0", "$zero", "$zero"],
            destination="$t0",
            instruction_type=InstructionType.ARITHMETIC,
        )

        rob_id = renaming.rename_instruction(instruction)
        assert rob_id is not None

        issued = renaming.issue_instructions()
        assert len(issued) == 1
        assert issued[0][0] == rob_id

    def test_branch_misprediction_recovery(self):
        """Test branch misprediction recovery."""
        config = {
            "arch_registers": 32,
            "physical_registers": 64,
            "rob_size": 32,
            "issue_queue_size": 16,
        }
        renaming = EnhancedRegisterRenaming(config)

        instructions = []
        for i in range(5):
            instruction = Instruction(
                address=0x1000 + i * 4,
                opcode="add",
                operands=[f"$t{i}", "$zero", "$zero"],
                destination=f"$t{i}",
                instruction_type=InstructionType.ARITHMETIC,
            )
            rob_id = renaming.rename_instruction(instruction)
            instructions.append((instruction, rob_id))

        assert renaming.rob_count == 5

        squashed = renaming.handle_branch_misprediction(2)
        assert squashed == 2
        assert renaming.rob_count == 3


# ============================================================================
# Power Modeling Tests
# ============================================================================


class TestPowerModeling:
    """Test power and energy modeling."""

    def test_component_power_model(self):
        """Test individual component power modeling."""
        params = PowerParameters(
            switching_capacitance=100.0,
            leakage_current=10.0,
            voltage=1.0,
            frequency=2.0,
        )
        component = ComponentPowerModel("test_core", params)

        dynamic_power = component.calculate_dynamic_power(0.5)
        static_power = component.calculate_static_power()

        assert dynamic_power > 0
        assert static_power > 0

        component.record_activity(1, "execute", 0.8)
        assert len(component.activity_events) == 1
        assert component.total_cycles == 1

    def test_processor_power_model(self):
        """Test complete processor power model."""
        config = {
            "technology_node": 45.0,
            "voltage": 1.0,
            "frequency": 2.0,
            "ambient_temp": 25.0,
        }
        power_model = ProcessorPowerModel(config)

        assert "core" in power_model.components
        assert "l1i_cache" in power_model.components
        assert "alu" in power_model.components

        instruction = Instruction(
            address=0x1000, opcode="add", instruction_type=InstructionType.ARITHMETIC
        )
        power_model.record_instruction_execution(instruction, "ALU_0")

        power_model.record_cache_access("1d", True, "read")

        for i in range(10):
            power_model.advance_cycle()

        stats = power_model.get_comprehensive_stats()
        assert "total_energy_pJ" in stats
        assert "average_power_mW" in stats
        assert "energy_per_instruction_pJ" in stats
        assert stats["instructions_executed"] == 1

    def test_power_breakdown(self):
        """Test power breakdown by component."""
        config = {}
        power_model = ProcessorPowerModel(config)

        instruction = Instruction(
            address=0x1000, opcode="add", instruction_type=InstructionType.ARITHMETIC
        )
        power_model.record_instruction_execution(instruction, "ALU_0")
        power_model.advance_cycle()

        breakdown = power_model.get_power_breakdown()
        assert "total_power_mW" in breakdown
        assert "core" in breakdown
        assert "core_percent" in breakdown

        total_percent = sum(v for k, v in breakdown.items() if k.endswith("_percent"))
        assert abs(total_percent - 100.0) < 0.1

    def test_energy_per_instruction(self):
        """Test Energy Per Instruction (EPI) calculation."""
        config = {}
        power_model = ProcessorPowerModel(config)

        assert power_model.get_energy_per_instruction() == 0.0

        for i in range(5):
            instruction = Instruction(
                address=0x1000 + i * 4,
                opcode="add",
                instruction_type=InstructionType.ARITHMETIC,
            )
            power_model.record_instruction_execution(instruction, "ALU_0")
            power_model.advance_cycle()

        epi = power_model.get_energy_per_instruction()
        assert epi > 0
        assert power_model.instructions_executed == 5


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration(unittest.TestCase):
    """Integration tests for all advanced features."""

    def test_configuration_with_profiling(self):
        """Test configuration system with profiling enabled."""
        config_manager = ConfigManager()

        config_dict = {
            "simulation": {
                "enable_profiling": True,
                "max_cycles": 1000,
            }
        }

        config = config_manager.create_from_dict(config_dict)

        self.assertTrue(config.simulation.enable_profiling)
        self.assertEqual(config.simulation.max_cycles, 1000)

    def test_error_handling_with_profiling(self):
        """Test error handling during profiling operations."""
        profiler = PerformanceProfiler()

        with self.assertRaises(RuntimeError):
            profiler.stop_profiling()

    def test_complete_workflow(self):
        """Test a complete workflow with all enhanced features."""
        config_manager = ConfigManager()
        config = config_manager.load_default()

        config.simulation.enable_profiling = True

        profiler = PerformanceProfiler()
        memory_profiler = MemoryProfiler()

        profiler.start_profiling()
        memory_profiler.start_profiling()

        try:
            data = []
            for i in range(config.simulation.max_cycles // 100):
                data.append(list(range(10)))

            perf_result = profiler.stop_profiling()
            mem_result = memory_profiler.stop_profiling()

            self.assertIsNotNone(perf_result)
            self.assertIsNotNone(mem_result)
            self.assertGreater(perf_result.execution_time, 0)

        except Exception as e:
            if isinstance(e, ConfigurationError):
                error_info = handle_simulator_error(e)
                self.assertIsInstance(error_info, dict)
            else:
                raise


class TestAdvancedFeaturesIntegration:
    """Test integration of advanced features."""

    def test_enhanced_features_integration(self):
        """Test that advanced features work together."""
        bp_config = {
            "tournament": {"predictor_1": {"size": 32}, "predictor_2": {"size": 32}},
            "adaptation_window": 100,
        }
        predictor = AdaptiveHybridPredictor(bp_config)

        cache_config = {
            "cache_size": 1024,
            "block_size": 64,
            "associativity": 2,
            "mshr_count": 4,
        }
        cache = NonBlockingCache(cache_config)

        renaming_config = {
            "arch_registers": 32,
            "physical_registers": 64,
            "rob_size": 16,
        }
        renaming = EnhancedRegisterRenaming(renaming_config)

        power_config = {}
        power_model = ProcessorPowerModel(power_config)

        assert predictor.predict(0x1000).taken in [True, False]
        cache.read(0x1000)

        instruction = Instruction(
            address=0x1000,
            opcode="add",
            operands=["$t0", "$t1", "$t2"],
            instruction_type=InstructionType.ARITHMETIC,
        )
        rob_id = renaming.rename_instruction(instruction)
        assert rob_id is not None

        power_model.record_instruction_execution(instruction, "ALU_0")

        assert True


if __name__ == "__main__":
    unittest.main()
