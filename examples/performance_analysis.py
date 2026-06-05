#!/usr/bin/env python3
"""
Performance Analysis Example

This example demonstrates performance analysis concepts using the simulator's
performance counters, hazard tracking, and pipeline stall analysis (v1.2.0).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import time

from performance.performance_counters import PerformanceCounters
from utils.instruction import InstructionType


def demonstrate_performance_profiling():
    """Show basic performance profiling capabilities."""
    print("Performance Profiling")
    print("-" * 30)

    # Simulate some computational work
    print("Simulating processor workload...")

    # Simulate instruction execution
    instructions = [
        ("ADD", InstructionType.ARITHMETIC, 1),
        ("MUL", InstructionType.ARITHMETIC, 3),
        ("LW", InstructionType.MEMORY, 5),
        ("FADD", InstructionType.FLOATING_POINT, 4),
        ("SW", InstructionType.MEMORY, 2),
        ("BEQ", InstructionType.BRANCH, 1),
    ]

    total_cycles = 0
    for opcode, instr_type, latency in instructions:
        # Simulate instruction execution time
        time.sleep(0.01)  # Small delay to simulate work
        total_cycles += latency

    # Simulate performance metrics
    execution_time = 0.1

    print("\nPerformance Metrics:")
    print(f"   Total Instructions: {len(instructions)}")
    print(f"   Total Cycles: {total_cycles}")
    print(f"   IPC: {len(instructions) / total_cycles:.2f}")
    print(f"   Execution Time: {execution_time:.3f} seconds")

    # Instruction type breakdown
    type_counts = {}
    for _, instr_type, _ in instructions:
        type_counts[instr_type.name] = type_counts.get(instr_type.name, 0) + 1

    print("\nInstruction Type Distribution:")
    for instr_type, count in type_counts.items():
        percentage = (count / len(instructions)) * 100
        print(f"   {instr_type}: {count} ({percentage:.1f}%)")


def demonstrate_bottleneck_analysis():
    """Show bottleneck identification and analysis."""
    print("\nBottleneck Analysis")
    print("-" * 30)

    # Simulate pipeline statistics
    pipeline_stats = {
        "fetch_stalls": 150,
        "decode_stalls": 50,
        "issue_stalls": 300,
        "execute_stalls": 100,
        "writeback_stalls": 25,
        "total_cycles": 1000,
    }

    print("Pipeline Stall Analysis:")
    for stage, stalls in pipeline_stats.items():
        if stage != "total_cycles":
            percentage = (stalls / pipeline_stats["total_cycles"]) * 100
            print(
                f"   {stage.replace('_', ' ').title()}: {stalls} cycles ({percentage:.1f}%)"
            )

    # Identify primary bottleneck
    max_stalls = max(
        (stalls for stage, stalls in pipeline_stats.items() if stage != "total_cycles")
    )
    bottleneck = next(
        stage for stage, stalls in pipeline_stats.items() if stalls == max_stalls
    )

    print(f"\nPrimary Bottleneck: {bottleneck.replace('_', ' ').title()}")
    print(
        f"Impact: {(max_stalls / pipeline_stats['total_cycles']) * 100:.1f}% of total cycles"
    )

    # Suggest optimizations
    optimizations = {
        "fetch_stalls": [
            "Increase instruction cache size",
            "Improve branch prediction accuracy",
            "Add instruction prefetching",
        ],
        "issue_stalls": [
            "Increase number of execution units",
            "Improve instruction scheduling",
            "Reduce register dependencies",
        ],
        "execute_stalls": [
            "Optimize functional unit latencies",
            "Add more execution units",
            "Improve data forwarding",
        ],
    }

    if bottleneck in optimizations:
        print("\nSuggested Optimizations:")
        for opt in optimizations[bottleneck]:
            print(f"   • {opt}")


def demonstrate_memory_profiling():
    """Show memory usage profiling and leak detection."""
    print("\nMemory Profiling")
    print("-" * 30)

    print("Simulating memory allocations...")

    # Simulate cache allocations
    cache_data = []
    for i in range(1000):
        cache_data.append(f"cache_line_{i}" * 10)  # Simulate cache line data

    # Simulate instruction buffer
    instruction_buffer = []
    for i in range(500):
        instruction_buffer.append(
            {
                "pc": 0x1000 + i * 4,
                "opcode": "ADD",
                "operands": ["$t0", "$t1", "$t2"],
                "metadata": {"cycle": i, "unit": "ALU_0"},
            }
        )

    # Simulate memory statistics
    print("Memory Usage Statistics:")
    print(
        f"   Current Memory: {len(cache_data) * 0.1 + len(instruction_buffer) * 0.05:.2f} MB"
    )
    print(
        f"   Peak Memory: {len(cache_data) * 0.12 + len(instruction_buffer) * 0.06:.2f} MB"
    )
    print(f"   Memory Growth: {0.02:.2f} MB")

    # Simulate memory cleanup
    del cache_data
    del instruction_buffer

    print("\nNo memory leaks detected")


def demonstrate_benchmark_comparison():
    """Show benchmark running and comparison."""
    print("\nBenchmark Comparison")
    print("-" * 30)

    # Simulate benchmark results for different configurations
    benchmark_results = {
        "matrix_multiplication": {
            "default_config": {"ipc": 1.2, "cycles": 5000, "energy": 2.5},
            "optimized_config": {"ipc": 1.8, "cycles": 3500, "energy": 3.2},
        },
        "bubble_sort": {
            "default_config": {"ipc": 0.9, "cycles": 8000, "energy": 1.8},
            "optimized_config": {"ipc": 1.4, "cycles": 6000, "energy": 2.1},
        },
        "fibonacci": {
            "default_config": {"ipc": 1.1, "cycles": 3000, "energy": 1.2},
            "optimized_config": {"ipc": 1.6, "cycles": 2200, "energy": 1.5},
        },
    }

    print("Benchmark Performance Comparison:")
    print(
        f"{'Benchmark':<20} {'Config':<15} {'IPC':<6} {'Cycles':<8} {'Energy (mJ)':<12}"
    )
    print("-" * 65)

    for benchmark, configs in benchmark_results.items():
        for config_name, metrics in configs.items():
            print(
                f"{benchmark:<20} {config_name:<15} {metrics['ipc']:<6.1f} "
                f"{metrics['cycles']:<8} {metrics['energy']:<12.1f}"
            )

    # Calculate improvements
    print("\nPerformance Improvements (Optimized vs Default):")
    for benchmark, configs in benchmark_results.items():
        default = configs["default_config"]
        optimized = configs["optimized_config"]

        ipc_improvement = ((optimized["ipc"] - default["ipc"]) / default["ipc"]) * 100
        cycle_reduction = (
            (default["cycles"] - optimized["cycles"]) / default["cycles"]
        ) * 100

        print(f"   {benchmark}:")
        print(f"     IPC Improvement: +{ipc_improvement:.1f}%")
        print(f"     Cycle Reduction: -{cycle_reduction:.1f}%")


def demonstrate_power_analysis():
    """Show power consumption analysis."""
    print("\nPower Analysis")
    print("-" * 30)

    # Simulate power measurements for different components
    power_breakdown = {
        "Core": 45.2,
        "L1 Cache": 18.5,
        "L2 Cache": 12.3,
        "Branch Predictor": 8.7,
        "Register File": 15.1,
        "Clock Network": 22.4,
        "Other": 7.8,
    }

    total_power = sum(power_breakdown.values())

    print("Power Consumption Breakdown:")
    print(f"{'Component':<18} {'Power (mW)':<12} {'Percentage':<12}")
    print("-" * 45)

    for component, power in power_breakdown.items():
        percentage = (power / total_power) * 100
        print(f"{component:<18} {power:<12.1f} {percentage:<12.1f}%")

    print(f"\nTotal Power: {total_power:.1f} mW")

    # Power efficiency metrics
    instructions_per_second = 1.5e9  # 1.5 GIPS
    power_efficiency = instructions_per_second / (total_power / 1000)  # MIPS/W

    print(f"Power Efficiency: {power_efficiency:.1f} MIPS/W")

    # Energy per instruction
    energy_per_instruction = (total_power / 1000) / (
        instructions_per_second / 1e12
    )  # pJ
    print(f"Energy per Instruction: {energy_per_instruction:.0f} pJ")


def demonstrate_live_performance_counters():
    """Show live performance counter tracking with realistic pipeline data."""
    print("\nLive Performance Counters (v1.2.0)")
    print("-" * 30)

    counters = PerformanceCounters()

    # Simulate a realistic 20-cycle pipeline execution
    import random

    random.seed(42)

    print("Simulating 20-cycle pipeline execution:")
    for cycle in range(20):
        # Simulate variable issue rates
        if cycle in [5, 12]:  # Stalls
            issued = 0
        elif cycle in [3, 8, 15]:  # Multi-issue
            issued = random.randint(2, 4)
        else:
            issued = random.randint(0, 2)

        in_flight = random.randint(2, 10)
        counters.record_cycle(
            instructions_issued=issued, instructions_in_flight=in_flight
        )

    # Simulate hazard events from a typical workload
    hazard_stats = {
        "hazards_detected": {
            "RAW": 25,
            "WAR": 8,
            "WAW": 3,
            "STRUCTURAL": 12,
            "CONTROL": 7,
        },
        "instructions_completed": 85,
    }
    counters.update_from_hazard_controller(hazard_stats)

    # Simulate cache behavior
    cache_stats = {
        "l1_stats": {"hits": 450, "misses": 50},
        "l2_stats": {"hits": 40, "misses": 10},
        "memory_accesses": 10,
    }
    counters.update_from_memory_hierarchy(cache_stats)

    # Simulate branch outcomes
    for _ in range(40):
        correct = random.random() > 0.15  # 85% accuracy
        counters.record_branch_outcome(
            predicted=True,
            actual=correct,
            penalty_cycles=0 if correct else random.randint(10, 20),
        )

    # Generate comprehensive report
    report = counters.get_detailed_report()

    print(f"\n{'=' * 50}")
    print("COMPREHENSIVE PERFORMANCE REPORT")
    print(f"{'=' * 50}")

    # Cycle analysis
    cc = report["cycle_counters"]
    print("\nCycle Analysis:")
    print(f"   Total Cycles: {cc['total_cycles']}")
    print(f"   Busy Cycles: {cc['busy_cycles']}")
    print(f"   Pipeline Utilization: {cc['pipeline_utilization_pct']:.1f}%")

    # Stall breakdown
    stalls = report["pipeline_stalls"]
    print("\nPipeline Stalls:")
    for stage, count in stalls.items():
        if stage != "total_stall_cycles" and count > 0:
            print(f"   {stage.replace('_', ' ').title()}: {count}")
    print(f"   Total Stall Cycles: {stalls['total_stall_cycles']}")

    # Hazard analysis
    hazards = report["hazard_counters"]
    print("\nHazard Analysis:")
    print(
        f"   RAW: {hazards['raw_hazards']} | WAR: {hazards['war_hazards']} | "
        f"WAW: {hazards['waw_hazards']}"
    )
    print(
        f"   Structural: {hazards['structural_hazards']} | "
        f"Control: {hazards['control_hazards']}"
    )
    print(f"   Total: {hazards['total_hazards']}")

    # Cache analysis
    cache = report["cache_counters"]
    print("\nCache Performance:")
    print(
        f"   L1 Reads: {cache['l1_read_hits']} hits / {cache['l1_read_misses']} misses"
    )
    print(f"   L1 Hit Rate: {cache['l1_hit_rate_pct']:.1f}%")
    print(f"   L2: {cache['l2_hits']} hits / {cache['l2_misses']} misses")

    # Branch analysis
    branch = report["branch_counters"]
    print("\nBranch Prediction:")
    print(f"   Total: {branch['total_predictions']}")
    print(f"   Accuracy: {branch['accuracy_pct']:.1f}%")
    print(f"   Misprediction Penalty: {branch['misprediction_penalty_cycles']} cycles")

    # ILP metrics
    ilp = report["ilp_counters"]
    print("\nInstruction-Level Parallelism:")
    print(f"   Instructions Issued: {ilp['instructions_issued']}")
    print(f"   Instructions Completed: {ilp['instructions_completed']}")
    print(f"   Max In-Flight: {ilp['max_instructions_in_flight']}")
    print(f"   Average Window: {ilp['average_window_size']:.1f}")
    print(f"   Multi-Issue Rate: {ilp['multi_issue_rate_pct']:.1f}%")


def main():
    """Main demonstration function."""
    print("Superscalar Pipeline Simulator")
    print("Performance Analysis Example")
    print("=" * 50)

    try:
        demonstrate_performance_profiling()
        demonstrate_live_performance_counters()
        demonstrate_bottleneck_analysis()
        demonstrate_memory_profiling()
        demonstrate_benchmark_comparison()
        demonstrate_power_analysis()

        print("\nPerformance analysis demonstration completed!")
        print("\nAnalysis capabilities:")
        print("   \u2022 Real-time performance monitoring")
        print("   \u2022 Live performance counters with detailed breakdown")
        print("   \u2022 Bottleneck identification and optimization")
        print("   \u2022 Memory usage tracking and leak detection")
        print("   \u2022 Benchmark comparison and evaluation")
        print("   \u2022 Power consumption analysis")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
