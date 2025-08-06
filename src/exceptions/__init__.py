"""
Custom exceptions for the Superscalar Pipeline Simulator.

This module provides a hierarchy of custom exceptions for better error handling
and debugging throughout the simulator.
"""

from .simulator_exceptions import (
    BranchPredictionError,
    CacheError,
    ConfigurationError,
    ExecutionError,
    HazardError,
    InstructionError,
    MemoryAccessError,
    MemoryError,
    PipelineError,
    PipelineStallError,
    RegisterFileError,
    SimulatorError,
    ValidationError,
    create_error_context,
    handle_simulator_error,
)

__all__ = [
    'SimulatorError',
    'ConfigurationError',
    'PipelineError',
    'PipelineStallError',
    'HazardError',
    'MemoryError',
    'MemoryAccessError',
    'CacheError',
    'BranchPredictionError',
    'InstructionError',
    'RegisterFileError',
    'ExecutionError',
    'ValidationError',
    'handle_simulator_error',
    'create_error_context',
]
