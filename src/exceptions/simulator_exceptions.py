"""
Custom exception hierarchy for the Superscalar Pipeline Simulator.

This module defines a comprehensive set of exceptions that provide better
error handling, debugging information, and recovery strategies.
"""

from __future__ import annotations

from typing import Any, Optional


class SimulatorError(Exception):
    """
    Base exception for all simulator-related errors.
    
    This is the root of the exception hierarchy and should be caught
    for general error handling.
    """
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize simulator error.
        
        Args:
            message: Human-readable error message
            details: Additional error details for debugging
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (Details: {detail_str})"
        return self.message


class ConfigurationError(SimulatorError):
    """
    Raised when configuration is invalid or cannot be loaded.
    
    This includes YAML parsing errors, validation failures, and
    missing configuration files.
    """
    pass


class PipelineError(SimulatorError):
    """
    Base class for pipeline-related errors.
    
    This covers errors in pipeline stages, instruction flow,
    and pipeline state management.
    """
    
    def __init__(self, message: str, stage: Optional[str] = None,
                 cycle: Optional[int] = None, **kwargs):
        """
        Initialize pipeline error.
        
        Args:
            message: Error message
            stage: Pipeline stage where error occurred
            cycle: Simulation cycle when error occurred
            **kwargs: Additional details
        """
        details = kwargs
        if stage:
            details['stage'] = stage
        if cycle is not None:
            details['cycle'] = cycle
        
        super().__init__(message, details)
        self.stage = stage
        self.cycle = cycle


class PipelineStallError(PipelineError):
    """
    Raised when pipeline encounters an unrecoverable stall.
    
    This indicates a deadlock or resource exhaustion that
    prevents further pipeline progress.
    """
    
    def __init__(self, message: str, stall_reason: str, **kwargs):
        """
        Initialize pipeline stall error.
        
        Args:
            message: Error message
            stall_reason: Reason for the stall
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.stall_reason = stall_reason
        self.details['stall_reason'] = stall_reason


class HazardError(PipelineError):
    """
    Raised when a hazard cannot be resolved.
    
    This includes data hazards, control hazards, and structural hazards
    that cannot be handled by the pipeline's hazard resolution mechanisms.
    """
    
    def __init__(self, message: str, hazard_type: str,
                 instructions: Optional[list[str]] = None, **kwargs):
        """
        Initialize hazard error.
        
        Args:
            message: Error message
            hazard_type: Type of hazard (RAW, WAR, WAW, control, structural)
            instructions: Instructions involved in the hazard
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.hazard_type = hazard_type
        self.instructions = instructions or []
        self.details['hazard_type'] = hazard_type
        if instructions:
            self.details['instructions'] = instructions


class MemoryError(SimulatorError):
    """
    Base class for memory system errors.
    
    This covers errors in memory access, cache operations,
    and memory management.
    """
    
    def __init__(self, message: str, address: Optional[int] = None, **kwargs):
        """
        Initialize memory error.
        
        Args:
            message: Error message
            address: Memory address where error occurred
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.address = address
        if address is not None:
            self.details['address'] = f"0x{address:x}"


class MemoryAccessError(MemoryError):
    """
    Raised for memory access violations.
    
    This includes out-of-bounds access, alignment errors,
    and permission violations.
    """
    
    def __init__(self, message: str, address: int, access_type: str, **kwargs):
        """
        Initialize memory access error.
        
        Args:
            message: Error message
            address: Memory address of the violation
            access_type: Type of access (read, write, execute)
            **kwargs: Additional details
        """
        super().__init__(message, address, **kwargs)
        self.access_type = access_type
        self.details['access_type'] = access_type


class CacheError(MemoryError):
    """
    Raised for cache-related errors.
    
    This includes cache coherency issues, invalid cache states,
    and cache configuration errors.
    """
    
    def __init__(self, message: str, cache_type: str, **kwargs):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            cache_type: Type of cache (instruction, data, unified)
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.cache_type = cache_type
        self.details['cache_type'] = cache_type


class BranchPredictionError(SimulatorError):
    """
    Raised for branch prediction errors.
    
    This includes predictor configuration errors and
    prediction table corruption.
    """
    
    def __init__(self, message: str, predictor_type: Optional[str] = None, **kwargs):
        """
        Initialize branch prediction error.
        
        Args:
            message: Error message
            predictor_type: Type of branch predictor
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.predictor_type = predictor_type
        if predictor_type:
            self.details['predictor_type'] = predictor_type


class InstructionError(SimulatorError):
    """
    Raised for instruction-related errors.
    
    This includes invalid instructions, unsupported opcodes,
    and instruction format errors.
    """
    
    def __init__(self, message: str, instruction: Optional[str] = None,
                 opcode: Optional[str] = None, **kwargs):
        """
        Initialize instruction error.
        
        Args:
            message: Error message
            instruction: Full instruction string
            opcode: Instruction opcode
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.instruction = instruction
        self.opcode = opcode
        if instruction:
            self.details['instruction'] = instruction
        if opcode:
            self.details['opcode'] = opcode


class RegisterFileError(SimulatorError):
    """
    Raised for register file errors.
    
    This includes invalid register names, register conflicts,
    and register file corruption.
    """
    
    def __init__(self, message: str, register: Optional[str] = None, **kwargs):
        """
        Initialize register file error.
        
        Args:
            message: Error message
            register: Register name or number
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.register = register
        if register:
            self.details['register'] = register


class ExecutionError(SimulatorError):
    """
    Raised for execution unit errors.
    
    This includes arithmetic errors, execution unit failures,
    and resource allocation errors.
    """
    
    def __init__(self, message: str, unit_type: Optional[str] = None,
                 operation: Optional[str] = None, **kwargs):
        """
        Initialize execution error.
        
        Args:
            message: Error message
            unit_type: Type of execution unit (ALU, FPU, LSU)
            operation: Operation being performed
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.unit_type = unit_type
        self.operation = operation
        if unit_type:
            self.details['unit_type'] = unit_type
        if operation:
            self.details['operation'] = operation


class ValidationError(SimulatorError):
    """
    Raised for validation errors.
    
    This includes input validation failures, state validation errors,
    and consistency check failures.
    """
    
    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            **kwargs: Additional details
        """
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)


# Exception handling utilities

def handle_simulator_error(error: SimulatorError, logger=None) -> dict[str, Any]:
    """
    Handle a simulator error and return structured error information.
    
    Args:
        error: The simulator error to handle
        logger: Optional logger for error reporting
        
    Returns:
        Dictionary with error information
    """
    error_info = {
        'type': error.__class__.__name__,
        'message': error.message,
        'details': error.details,
    }
    
    if logger:
        logger.error(f"{error_info['type']}: {error_info['message']}",
                    extra={'error_details': error_info['details']})
    
    return error_info


def create_error_context(stage: Optional[str] = None, cycle: Optional[int] = None,
                        instruction: Optional[str] = None) -> dict[str, Any]:
    """
    Create error context dictionary for consistent error reporting.
    
    Args:
        stage: Current pipeline stage
        cycle: Current simulation cycle
        instruction: Current instruction
        
    Returns:
        Context dictionary
    """
    context = {}
    
    if stage:
        context['stage'] = stage
    if cycle is not None:
        context['cycle'] = cycle
    if instruction:
        context['instruction'] = instruction
    
    return context
