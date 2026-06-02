#!/usr/bin/env python3
"""
Basic Simulation Example

This example demonstrates how to set up and run a basic simulation
using the superscalar pipeline simulator with default configuration.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.config_manager import ConfigManager
from profiling.performance_profiler import PerformanceProfiler
from utils.instruction_parser import MIPSInstructionParser


def run_basic_simulation():
    """Run a basic simulation with simple assembly code."""
    
    print("Superscalar Pipeline Simulator - Basic Example")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = ConfigManager()
    config = config_manager.load_default()
    
    # Simple assembly program
    assembly_code = """
    # Basic arithmetic operations
    li $t0, 10
    li $t1, 20
    add $t2, $t0, $t1
    sub $t3, $t2, $t1
    
    # Memory operations
    sw $t2, 0($sp)
    lw $t4, 0($sp)
    
    # Branch operation
    beq $t2, $t4, end
    li $t5, 99
    
    end:
    li $v0, 10
    syscall
    """
    
    # Parse instructions
    parser = MIPSInstructionParser()
    try:
        instructions = parser.parse_program(assembly_code)
        print(f"Parsed {len(instructions)} instructions successfully")
        
        # Display parsed instructions
        print("\nParsed Instructions:")
        for i, instr in enumerate(instructions):
            print(f"  {i}: {instr.opcode} {', '.join(map(str, instr.operands))}")
        
    except Exception as e:
        print(f"Error parsing assembly: {e}")
        return
    
    # Initialize profiler
    profiler = PerformanceProfiler()
    profiler.start_profiling()
    
    # Simulate basic execution metrics
    print("\nSimulation Configuration:")
    print(f"  Pipeline Width: {getattr(config.pipeline, 'width', 4)}")
    print(f"  Cache Size: {getattr(config.memory.data_cache, 'size', 32768) // 1024} KB")
    print(f"  Branch Predictor: {getattr(config.branch_predictor, 'type', 'bimodal')}")
    
    # Simulate execution
    cycles = len(instructions) * 2  # Simplified cycle calculation
    ipc = len(instructions) / cycles
    
    print("\nSimulation Results:")
    print(f"  Instructions: {len(instructions)}")
    print(f"  Cycles: {cycles}")
    print(f"  IPC: {ipc:.2f}")
    
    profiler.stop_profiling()
    
    print("\nBasic simulation completed successfully!")


if __name__ == "__main__":
    run_basic_simulation()
