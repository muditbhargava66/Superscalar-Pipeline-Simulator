"""
Cache and memory system components for the superscalar processor simulator.

This module provides instruction cache, data cache, and main memory
implementations with configurable parameters.
"""

from .cache import DataCache, InstructionCache, Memory

__all__ = [
    'InstructionCache',
    'DataCache',
    'Memory'
]
