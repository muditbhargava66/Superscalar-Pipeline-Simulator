"""
Performance profiling and analysis tools for the Superscalar Pipeline Simulator.

This module provides comprehensive profiling capabilities including:
- Execution time profiling
- Memory usage analysis
- Performance bottleneck identification
- Comparative analysis tools
"""

from .benchmark_runner import BenchmarkConfig, BenchmarkRunner
from .memory_profiler import MemoryProfiler
from .performance_profiler import (
    BottleneckAnalyzer,
    PerformanceProfiler,
    ProfileResult,
)

__all__ = [
    'PerformanceProfiler',
    'ProfileResult',
    'BottleneckAnalyzer',
    'MemoryProfiler',
    'BenchmarkRunner',
    'BenchmarkConfig',
]
