"""
Register file implementation for the superscalar processor simulator.

This module provides the register file with support for multiple read/write
ports and register locking for hazard prevention.
"""

from .register_file import RegisterFile

__all__ = ['RegisterFile']
