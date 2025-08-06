#!/usr/bin/env python3
"""
Example demonstrating the enhanced error handling system.

This example shows how to use the new exception hierarchy and
error handling utilities for robust simulator operation.
"""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from exceptions import (
    ConfigurationError,
    InstructionError,
    MemoryAccessError,
    PipelineError,
    SimulatorError,
    create_error_context,
    handle_simulator_error,
)


def demonstrate_configuration_error():
    """Demonstrate configuration error handling."""
    print("1. Configuration Error Example")
    print("-" * 30)
    
    try:
        # Simulate a configuration error
        raise ConfigurationError(
            "Invalid pipeline configuration",
            details={
                'field': 'fetch_width',
                'value': 0,
                'expected': 'positive integer'
            }
        )
    except ConfigurationError as e:
        print(f"✅ Caught configuration error: {e}")
        print(f"   Details: {e.details}")
        
        # Use error handling utility
        error_info = handle_simulator_error(e)
        print(f"   Structured info: {error_info}")


def demonstrate_pipeline_error():
    """Demonstrate pipeline error handling."""
    print("\n2. Pipeline Error Example")
    print("-" * 25)
    
    try:
        # Create error context
        create_error_context(
            stage='execute',
            cycle=150,
            instruction='ADD $t0, $t1, $t2'
        )
        
        # Simulate a pipeline error
        raise PipelineError(
            "Pipeline stall detected",
            stage='execute',
            cycle=150,
            stall_reason='resource_conflict'
        )
    except PipelineError as e:
        print(f"✅ Caught pipeline error: {e}")
        print(f"   Stage: {e.stage}")
        print(f"   Cycle: {e.cycle}")
        print(f"   Details: {e.details}")


def demonstrate_memory_error():
    """Demonstrate memory access error handling."""
    print("\n3. Memory Access Error Example")
    print("-" * 30)
    
    try:
        # Simulate a memory access violation
        raise MemoryAccessError(
            "Memory access out of bounds",
            address=0x10000000,
            access_type='read',
            details={
                'memory_size': 0x1000000,
                'instruction': 'LW $t0, 0($t1)'
            }
        )
    except MemoryAccessError as e:
        print(f"✅ Caught memory access error: {e}")
        print(f"   Address: {e.address:#x}")
        print(f"   Access type: {e.access_type}")
        print(f"   Details: {e.details}")


def demonstrate_instruction_error():
    """Demonstrate instruction error handling."""
    print("\n4. Instruction Error Example")
    print("-" * 25)
    
    try:
        # Simulate an invalid instruction
        raise InstructionError(
            "Unsupported instruction opcode",
            instruction="INVALID $t0, $t1, $t2",
            opcode="INVALID",
            details={
                'supported_opcodes': ['ADD', 'SUB', 'MUL', 'DIV'],
                'line_number': 42
            }
        )
    except InstructionError as e:
        print(f"✅ Caught instruction error: {e}")
        print(f"   Instruction: {e.instruction}")
        print(f"   Opcode: {e.opcode}")
        print(f"   Details: {e.details}")


def demonstrate_error_recovery():
    """Demonstrate error recovery strategies."""
    print("\n5. Error Recovery Example")
    print("-" * 25)
    
    def risky_operation(should_fail: bool = False):
        """Simulate a risky operation that might fail."""
        if should_fail:
            raise PipelineError(
                "Simulated pipeline failure",
                stage='decode',
                cycle=100
            )
        return "Operation successful"
    
    # Strategy 1: Retry with fallback
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = risky_operation(should_fail=(attempt < 2))
            print(f"✅ Operation succeeded on attempt {attempt + 1}: {result}")
            break
        except PipelineError as e:
            print(f"⚠️  Attempt {attempt + 1} failed: {e.message}")
            if attempt == max_retries - 1:
                print("❌ All retry attempts exhausted")
                raise
    
    # Strategy 2: Graceful degradation
    try:
        risky_operation(should_fail=True)
    except PipelineError as e:
        print(f"⚠️  Operation failed, using fallback: {e.message}")
        fallback_result = "Fallback operation result"
        print(f"✅ Fallback successful: {fallback_result}")


def demonstrate_nested_errors():
    """Demonstrate handling of nested errors."""
    print("\n6. Nested Error Example")
    print("-" * 22)
    
    def level_3_function():
        """Third level function that raises an error."""
        raise MemoryAccessError(
            "Cache miss on critical data",
            address=0x1000,
            access_type='read'
        )
    
    def level_2_function():
        """Second level function that catches and re-raises."""
        try:
            level_3_function()
        except MemoryAccessError as e:
            raise PipelineError(
                "Memory access failed during execution",
                stage='memory',
                cycle=200
            ) from e
    
    def level_1_function():
        """Top level function that handles the final error."""
        try:
            level_2_function()
        except PipelineError as e:
            print(f"✅ Caught nested error: {e}")
            print(f"   Original cause: {e.__cause__}")
            
            # Handle the error chain
            current_error = e
            level = 1
            while current_error:
                print(f"   Level {level}: {current_error.__class__.__name__}: {current_error}")
                current_error = current_error.__cause__
                level += 1
    
    level_1_function()


def demonstrate_error_context():
    """Demonstrate error context creation and usage."""
    print("\n7. Error Context Example")
    print("-" * 23)
    
    # Create rich error context
    context = create_error_context(
        stage='issue',
        cycle=75,
        instruction='MUL $t0, $t1, $t2'
    )
    
    print(f"✅ Created error context: {context}")
    
    # Use context in error creation
    try:
        raise PipelineError(
            "Reservation station full",
            **context,
            available_stations=0,
            required_stations=1
        )
    except PipelineError as e:
        print(f"✅ Error with context: {e}")
        print(f"   Context details: {e.details}")


def main():
    """Run all error handling demonstrations."""
    print("Enhanced Error Handling Examples")
    print("=" * 40)
    
    try:
        demonstrate_configuration_error()
        demonstrate_pipeline_error()
        demonstrate_memory_error()
        demonstrate_instruction_error()
        demonstrate_error_recovery()
        demonstrate_nested_errors()
        demonstrate_error_context()
        
        print("\n" + "=" * 40)
        print("All error handling examples completed successfully!")
        
        print("\nKey takeaways:")
        print("- Use specific exception types for different error categories")
        print("- Include detailed context information in errors")
        print("- Use error handling utilities for consistent error processing")
        print("- Implement retry and fallback strategies where appropriate")
        print("- Preserve error chains for debugging nested failures")
        
    except Exception as e:
        print(f"\n❌ Unexpected error in demonstration: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
