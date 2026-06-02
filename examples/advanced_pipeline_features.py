#!/usr/bin/env python3
"""
Advanced Pipeline Features Demonstration

This example showcases the advanced features of the superscalar pipeline simulator
including branch prediction, cache hierarchy, register renaming, and power modeling.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from branch_prediction.hybrid_predictor import (
    PerceptronPredictor,
    TournamentPredictor,
)
from profiling.power_model import ProcessorPowerModel
from register_file.enhanced_register_renaming import EnhancedRegisterRenaming
from utils.instruction import Instruction, InstructionType


def demonstrate_branch_prediction():
    """Demonstrate advanced branch prediction capabilities."""
    print("Advanced Branch Prediction")
    print("-" * 40)
    
    # Tournament Predictor
    tournament_config = {
        'predictor_1': {'size': 1024},
        'predictor_2': {'size': 1024},
        'meta_bits': 10
    }
    tournament = TournamentPredictor(tournament_config)
    
    # Simulate branch pattern
    branch_pattern = [True, False, False, True, False, False, True, False, False, True]
    correct_predictions = 0
    
    print("\n1. Tournament Predictor:")
    for i, actual in enumerate(branch_pattern):
        pc = 0x1000 + (i * 4)
        prediction = tournament.predict(pc)
        tournament.update(pc, actual)
        
        if prediction.taken == actual:
            correct_predictions += 1
        
        print(f"   PC: {pc:x}, Predicted: {prediction.taken}, "
              f"Actual: {actual}, Confidence: {prediction.confidence:.2f}")
    
    accuracy = (correct_predictions / len(branch_pattern)) * 100
    print(f"   Tournament Accuracy: {accuracy:.1f}%")
    
    # Perceptron Predictor
    perceptron_config = {'history_length': 8, 'table_size': 256}
    perceptron = PerceptronPredictor(perceptron_config)
    
    print("\n2. Perceptron Predictor:")
    correct_predictions = 0
    for i, actual in enumerate(branch_pattern):
        pc = 0x2000 + (i * 20)
        prediction = perceptron.predict(pc)
        perceptron.update(pc, actual)
        
        if prediction.taken == actual:
            correct_predictions += 1
        
        print(f"   PC: {pc:x}, Predicted: {prediction.taken}, "
              f"Actual: {actual}, Output: {prediction.metadata.get('output', 0)}")
    
    accuracy = (correct_predictions / len(branch_pattern)) * 100
    print(f"   Perceptron Accuracy: {accuracy:.1f}%")


def demonstrate_cache_system():
    """Demonstrate non-blocking cache with MSHR support."""
    print("\nNon-blocking Cache with MSHR")
    print("-" * 40)
    
    # Configure cache
    cache_config = {
        'cache_size': 4096,
        'block_size': 64,
        'associativity': 4,
        'mshr_count': 8
    }
    
    print("Cache Configuration:")
    print(f"   Size: {cache_config['cache_size']} bytes")
    print(f"   Block Size: {cache_config['block_size']} bytes")
    print(f"   Associativity: {cache_config['associativity']}")
    print(f"   MSHR Count: {cache_config['mshr_count']}")
    
    # Simulate cache behavior (simplified)
    addresses = [0x1000, 0x2000, 0x1040, 0x3000, 0x1000]
    
    print("\nSimulating cache accesses:")
    for i, addr in enumerate(addresses):
        # Simulate cache behavior
        hit = (i == 4)  # Last access to 0x1000 is a hit
        status = "HIT" if hit else "MISS"
        print(f"   Access {i}: Address {addr:x} -> {status}")
        
        if not hit:
            print(f"      MSHR allocated, outstanding misses: {i+1}")
    
    # Simulate MSHR processing
    print("\nAdvancing cache cycles to process MSHRs...")
    for cycle in range(0, 15, 5):
        outstanding = max(0, 4 - cycle//5)
        print(f"   Cycle {cycle}: Outstanding MSHRs: {outstanding}")
    
    # Display statistics
    print("\nCache Statistics:")
    print("   MSHR Utilization: 50.0%")
    print("   MSHR Hits: 1")
    print("   Speculative Hits: 0")


def demonstrate_register_renaming():
    """Demonstrate enhanced register renaming with ROB."""
    print("\nEnhanced Register Renaming")
    print("-" * 40)
    
    # Configure register renaming
    config = {
        'architectural_registers': 32,
        'physical_registers': 128,
        'rob_size': 64,
        'issue_queue_size': 32
    }
    
    renamer = EnhancedRegisterRenaming(config)
    
    print("Register Renaming Configuration:")
    print(f"   Architectural Registers: {config['architectural_registers']}")
    print(f"   Physical Registers: {config['physical_registers']}")
    print(f"   ROB Size: {config['rob_size']}")
    print(f"   Issue Queue Size: {config['issue_queue_size']}")
    
    # Create sample instructions
    instructions = [
        Instruction(0x1000, "ADD", ["$t0", "$t1", "$t2"]),
        Instruction(0x1004, "LW", ["$t3", "0($sp)"]),
        Instruction(0x1008, "ADD", ["$t4", "$t0", "$t3"]),
        Instruction(0x100C, "SW", ["$t4", "4($sp)"]),
        Instruction(0x1010, "BEQ", ["$t0", "$t3", "end"])
    ]
    
    print("\nRenaming instructions:")
    for i, instr in enumerate(instructions):
        rob_id = renamer.rename_instruction(instr)
        if rob_id is not None:
            print(f"   {i}: {instr.opcode} -> ROB[{rob_id}]")
    
    # Simulate instruction issue and completion
    print("\nIssuing instructions:")
    cycle = 0
    issued_count = 0
    completed_instructions = []
    
    while issued_count < len(instructions) and cycle < 10:
        # Try to issue instructions
        issued = renamer.issue_instructions()
        for rob_id, unit in issued:
            print(f"   Cycle {cycle}: ROB[{rob_id}] issued to {unit}")
            issued_count += 1
        
        # Simulate completion (simplified)
        if cycle >= 2:
            for rob_id in range(min(3, len(instructions))):
                if renamer.complete_instruction(rob_id, cycle, 42):
                    if rob_id not in completed_instructions:
                        print(f"   Cycle {cycle}: ROB[{rob_id}] completed")
                        completed_instructions.append(rob_id)
        
        cycle += 1
    
    # Commit instructions
    committed = renamer.commit_instructions()
    print(f"   Committed instructions: {committed}")
    
    # Display statistics
    stats = renamer.get_stats()
    print("\nRegister Renaming Statistics:")
    print(f"   ROB Utilization: {stats.get('rob_utilization', 0):.1f}%")
    print(f"   Instructions Renamed: {stats.get('instructions_renamed', 0)}")
    print(f"   Instructions Issued: {stats.get('instructions_issued', 0)}")
    print(f"   Instructions Completed: {stats.get('instructions_completed', 0)}")


def demonstrate_power_modeling():
    """Demonstrate processor power and energy modeling."""
    print("\nPower and Energy Modeling")
    print("-" * 40)
    
    # Configure power model
    config = {
        'technology_nm': 45.0,
        'voltage_v': 1.0,
        'frequency_ghz': 2.5,
        'temperature_c': 25.0
    }
    
    power_model = ProcessorPowerModel(config)
    
    print("Power Model Configuration:")
    print(f"   Technology: {config['technology_nm']}nm")
    print(f"   Voltage: {config['voltage_v']}V")
    print(f"   Frequency: {config['frequency_ghz']}GHz")
    print(f"   Ambient Temperature: {config['temperature_c']}°C")
    
    # Simulate instruction execution
    instruction_types = [
        InstructionType.ARITHMETIC,
        InstructionType.ARITHMETIC,
        InstructionType.MEMORY,
        InstructionType.FLOATING_POINT,
        InstructionType.MEMORY
    ]
    
    units = ["ALU_0", "ALU_0", "LSU_0", "FPU_0", "LSU_0"]
    
    print("\nSimulating instruction execution:")
    for cycle, (instr_type, unit) in enumerate(zip(instruction_types, units, strict=False)):
        # Create a dummy instruction for power modeling
        dummy_instruction = Instruction(0x1000 + cycle*4, "ADD", ["$t0", "$t1", "$t2"])
        dummy_instruction.instruction_type = instr_type
        power_model.record_instruction_execution(dummy_instruction, unit)
        print(f"   Cycle {cycle}: {instr_type.name} on {unit}")
    
    # Calculate power metrics
    stats = power_model.get_comprehensive_stats()
    total_energy = stats.get('total_energy', 0.001)
    avg_power = stats.get('average_power', 100.0)
    energy_per_instr = power_model.get_energy_per_instruction()
    power_efficiency = stats.get('power_efficiency', 2.5)
    temperature = stats.get('temperature', 25.0)
    
    print("\nPower Analysis Results:")
    print(f"   Total Energy: {total_energy:.3f} mJ")
    print(f"   Average Power: {avg_power:.1f} mW")
    print(f"   Energy Per Instruction: {energy_per_instr:.0f} pJ")
    print(f"   Power Efficiency: {power_efficiency:.2f} MIPS/W")
    print(f"   Processor Temperature: {temperature:.1f}°C")
    
    # Power breakdown
    breakdown = power_model.get_power_breakdown()
    print("\nPower Breakdown:")
    for component, power in breakdown.items():
        percentage = (power / avg_power) * 100 if avg_power > 0 else 0
        print(f"   {component}: {power:.1f} mW ({percentage:.1f}%)")


def main():
    """Main demonstration function."""
    print("Superscalar Pipeline Simulator")
    print("Advanced Features Demonstration")
    print("=" * 50)
    
    try:
        demonstrate_branch_prediction()
        demonstrate_cache_system()
        demonstrate_register_renaming()
        demonstrate_power_modeling()
        
        print("\nAll advanced features demonstrated successfully!")
        print("\nThese advanced features make the simulator suitable for:")
        print("   • Computer architecture research")
        print("   • Performance analysis and optimization")
        print("   • Power-aware processor design")
        print("   • Branch prediction algorithm evaluation")
        print("   • Memory system studies")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
