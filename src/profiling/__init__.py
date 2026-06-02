"""
Enhanced performance profiling and analysis tools for the Superscalar Pipeline Simulator.

This module provides comprehensive profiling capabilities including:
- Execution time profiling
- Memory usage analysis
- Performance bottleneck identification
- Comparative analysis tools
- Power and energy modeling
"""

from .benchmark_runner import BenchmarkConfig, BenchmarkRunner
from .memory_profiler import MemoryProfiler
from .performance_profiler import (
    BottleneckAnalyzer,
    PerformanceProfiler,
    ProfileResult,
)
from .power_model import ComponentPowerModel, ProcessorPowerModel

__all__ = [
    "BenchmarkConfig",
    "BenchmarkRunner",
    "BottleneckAnalyzer",
    "ComponentPowerModel",
    "MemoryProfiler",
    "PerformanceProfiler",
    "ProcessorPowerModel",
    "ProfileResult",
]
