"""
Superscalar Pipeline Simulator Package

A comprehensive superscalar processor pipeline simulator with advanced features
including branch prediction, data forwarding, and performance profiling.
"""

__version__ = "1.0.0"
__author__ = "Mudit Bhargava"

# Import main components for easy access
from .config import ConfigManager, SimulatorConfig
from .exceptions import SimulatorError
from .profiling import MemoryProfiler, PerformanceProfiler

__all__ = [
    'ConfigManager',
    'SimulatorConfig',
    'SimulatorError',
    'PerformanceProfiler',
    'MemoryProfiler',
]
