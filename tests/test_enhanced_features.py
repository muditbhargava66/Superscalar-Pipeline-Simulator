"""
Integration tests for the enhanced features.

This module tests the new configuration management, error handling,
and profiling capabilities.
"""

import os
from pathlib import Path

# Add src to path for imports
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager, PipelineConfig, SimulatorConfig
from exceptions import (
    ConfigurationError,
    MemoryAccessError,
    PipelineError,
    handle_simulator_error,
)
from profiling import MemoryProfiler, PerformanceProfiler


class TestEnhancedConfiguration(unittest.TestCase):
    """Test the enhanced configuration management system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        for file in self.temp_dir.glob('*'):
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
        # Valid configuration should pass
        valid_config = {
            'pipeline': {
                'num_stages': 5,
                'fetch_width': 4,
                'issue_width': 4,
            }
        }
        
        config = self.config_manager.create_from_dict(valid_config)
        self.assertEqual(config.pipeline.num_stages, 5)
        
        # Invalid configuration should fail
        invalid_config = {
            'pipeline': {
                'num_stages': 15,  # Too many stages
                'fetch_width': 0,  # Too small
            }
        }
        
        with self.assertRaises(ConfigurationError):
            self.config_manager.create_from_dict(invalid_config)
    
    def test_environment_variable_overrides(self):
        """Test environment variable configuration overrides."""
        # Set environment variables
        os.environ['SIMULATOR_PIPELINE__FETCH_WIDTH'] = '8'
        os.environ['SIMULATOR_DEBUG__ENABLED'] = 'true'
        
        try:
            config = self.config_manager.load_default()
            
            self.assertEqual(config.pipeline.fetch_width, 8)
            self.assertTrue(config.debug.enabled)
        finally:
            # Clean up environment variables
            os.environ.pop('SIMULATOR_PIPELINE__FETCH_WIDTH', None)
            os.environ.pop('SIMULATOR_DEBUG__ENABLED', None)
    
    def test_configuration_file_operations(self):
        """Test configuration file loading and saving."""
        # Create a test configuration
        config = self.config_manager.load_default()
        config.pipeline.fetch_width = 6
        
        # Save to file
        config_file = self.temp_dir / 'test_config.yaml'
        config.save_to_file(config_file)
        
        self.assertTrue(config_file.exists())
        
        # Load from file
        loaded_config = self.config_manager.load_from_file(config_file)
        self.assertEqual(loaded_config.pipeline.fetch_width, 6)
    
    def test_configuration_validation_utility(self):
        """Test configuration file validation utility."""
        # Create valid config file
        config = self.config_manager.load_default()
        valid_config_file = self.temp_dir / 'valid_config.yaml'
        config.save_to_file(valid_config_file)
        
        # Validate valid config
        is_valid, errors = self.config_manager.validate_config_file(valid_config_file)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Create invalid config file
        invalid_config_file = self.temp_dir / 'invalid_config.yaml'
        with open(invalid_config_file, 'w') as f:
            f.write("pipeline:\n  num_stages: 15\n  fetch_width: 0\n")
        
        # Validate invalid config
        is_valid, errors = self.config_manager.validate_config_file(invalid_config_file)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestEnhancedErrorHandling(unittest.TestCase):
    """Test the enhanced error handling system."""
    
    def test_simulator_error_hierarchy(self):
        """Test the exception hierarchy."""
        # Test base exception
        base_error = ConfigurationError("Test error", details={'key': 'value'})
        self.assertEqual(base_error.message, "Test error")
        self.assertEqual(base_error.details['key'], 'value')
        
        # Test inheritance
        self.assertIsInstance(base_error, ConfigurationError)
        
        # Test string representation
        error_str = str(base_error)
        self.assertIn("Test error", error_str)
        self.assertIn("key=value", error_str)
    
    def test_pipeline_error_context(self):
        """Test pipeline error with context."""
        error = PipelineError(
            "Test pipeline error",
            stage='execute',
            cycle=100,
            instruction='ADD $t0, $t1, $t2'
        )
        
        self.assertEqual(error.stage, 'execute')
        self.assertEqual(error.cycle, 100)
        self.assertEqual(error.details['stage'], 'execute')
        self.assertEqual(error.details['cycle'], 100)
    
    def test_memory_access_error(self):
        """Test memory access error."""
        error = MemoryAccessError(
            "Out of bounds access",
            address=0x10000,
            access_type='read'
        )
        
        self.assertEqual(error.address, 0x10000)
        self.assertEqual(error.access_type, 'read')
        self.assertEqual(error.details['address'], '0x10000')
        self.assertEqual(error.details['access_type'], 'read')
    
    def test_error_handling_utility(self):
        """Test error handling utility function."""
        error = PipelineError(
            "Test error",
            stage='decode',
            cycle=50
        )
        
        # Mock logger
        mock_logger = MagicMock()
        
        error_info = handle_simulator_error(error, mock_logger)
        
        self.assertEqual(error_info['type'], 'PipelineError')
        self.assertEqual(error_info['message'], 'Test error')
        self.assertEqual(error_info['details']['stage'], 'decode')
        
        # Verify logger was called
        mock_logger.error.assert_called_once()


class TestPerformanceProfiling(unittest.TestCase):
    """Test the performance profiling system."""
    
    def test_performance_profiler_basic(self):
        """Test basic performance profiler functionality."""
        profiler = PerformanceProfiler(enable_detailed_profiling=False)
        
        # Test profiling context manager
        with profiler.profile_simulation() as session:
            # Simulate some work
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
        
        # Simulate some work
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
            # Simulate CPU-intensive work
            total = 0
            for i in range(10000):
                total += i * i
        
        result = session.get_results()
        
        # Should have some analysis results
        self.assertIsInstance(result.bottlenecks, list)
        self.assertIsInstance(result.recommendations, list)


class TestMemoryProfiling(unittest.TestCase):
    """Test the memory profiling system."""
    
    def test_memory_profiler_basic(self):
        """Test basic memory profiler functionality."""
        profiler = MemoryProfiler(track_allocations=False)
        
        profiler.start_profiling()
        
        # Simulate memory usage
        [list(range(100)) for _ in range(100)]
        
        result = profiler.stop_profiling()
        
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.memory_growth, 0)
        self.assertGreater(result.peak_memory, 0)
    
    def test_memory_profiler_with_tracking(self):
        """Test memory profiler with allocation tracking."""
        profiler = MemoryProfiler(track_allocations=True)
        
        profiler.start_profiling()
        
        # Take snapshots
        profiler.take_snapshot()
        
        # Allocate memory
        [list(range(1000)) for _ in range(100)]
        
        profiler.take_snapshot()
        
        result = profiler.stop_profiling()
        
        self.assertIsNotNone(result)
        self.assertGreater(result.memory_growth, 0)
        self.assertGreaterEqual(len(result.potential_leaks), 0)
        self.assertIsInstance(result.recommendations, list)


class TestIntegration(unittest.TestCase):
    """Integration tests for all enhanced features together."""
    
    def test_configuration_with_profiling(self):
        """Test configuration system with profiling enabled."""
        config_manager = ConfigManager()
        
        # Create config with profiling enabled
        config_dict = {
            'simulation': {
                'enable_profiling': True,
                'max_cycles': 1000,
            }
        }
        
        config = config_manager.create_from_dict(config_dict)
        
        self.assertTrue(config.simulation.enable_profiling)
        self.assertEqual(config.simulation.max_cycles, 1000)
    
    def test_error_handling_with_profiling(self):
        """Test error handling during profiling operations."""
        profiler = PerformanceProfiler()
        
        # Test error during profiling
        with self.assertRaises(RuntimeError):
            # Try to stop profiling without starting
            profiler.stop_profiling()
    
    def test_complete_workflow(self):
        """Test a complete workflow with all enhanced features."""
        # 1. Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_default()
        
        # 2. Enable profiling
        config.simulation.enable_profiling = True
        
        # 3. Start profiling
        profiler = PerformanceProfiler()
        memory_profiler = MemoryProfiler()
        
        profiler.start_profiling()
        memory_profiler.start_profiling()
        
        try:
            # 4. Simulate some work
            data = []
            for i in range(config.simulation.max_cycles // 100):
                data.append(list(range(10)))
            
            # 5. Stop profiling
            perf_result = profiler.stop_profiling()
            mem_result = memory_profiler.stop_profiling()
            
            # 6. Verify results
            self.assertIsNotNone(perf_result)
            self.assertIsNotNone(mem_result)
            self.assertGreater(perf_result.execution_time, 0)
            
        except Exception as e:
            # 7. Handle errors properly
            if isinstance(e, ConfigurationError):
                error_info = handle_simulator_error(e)
                self.assertIsInstance(error_info, dict)
            else:
                raise


if __name__ == '__main__':
    unittest.main()
