#!/usr/bin/env python3
"""
Example demonstrating the performance profiling tools.

This example shows how to use the new profiling capabilities including
performance profiling, memory profiling, and benchmark running.
"""

from pathlib import Path
import sys
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from profiling import (
    BenchmarkConfig,
    BenchmarkRunner,
    MemoryProfiler,
    PerformanceProfiler,
)


def simulate_cpu_intensive_work():
    """Simulate CPU-intensive work for profiling demonstration."""
    # Simulate some computational work
    total = 0
    for i in range(100000):
        total += i * i
    return total


def simulate_memory_intensive_work():
    """Simulate memory-intensive work for profiling demonstration."""
    # Create and manipulate large data structures
    data = []
    for i in range(10000):
        data.append(list(range(100)))
    
    # Process the data
    result = []
    for sublist in data:
        result.append(sum(sublist))
    
    return result


def main():
    """Demonstrate profiling features."""
    print("Performance Profiling Example")
    print("=" * 40)
    
    # 1. Performance Profiling Example
    print("\n1. Performance Profiling Demo")
    print("-" * 30)
    
    profiler = PerformanceProfiler(enable_detailed_profiling=True)
    
    # Use context manager for profiling
    with profiler.profile_simulation() as session:
        print("Running CPU-intensive simulation...")
        simulate_cpu_intensive_work()
        
        print("Running memory-intensive simulation...")
        simulate_memory_intensive_work()
        
        # Simulate some delay
        time.sleep(0.1)
    
    # Get profiling results
    profile_result = session.get_results()
    
    print("✅ Profiling completed!")
    print(f"   Execution time: {profile_result.execution_time:.3f}s")
    print(f"   CPU utilization: {profile_result.cpu_usage.get('cpu_utilization', 0):.1f}%")
    print(f"   Memory growth: {profile_result.memory_usage.get('memory_growth', 0):.1f}MB")
    print(f"   Bottlenecks found: {len(profile_result.bottlenecks)}")
    
    if profile_result.bottlenecks:
        print("   Bottlenecks:")
        for bottleneck in profile_result.bottlenecks:
            print(f"     - {bottleneck['description']} (Severity: {bottleneck['severity']})")
    
    if profile_result.recommendations:
        print("   Recommendations:")
        for rec in profile_result.recommendations[:3]:  # Show first 3
            print(f"     - {rec}")
    
    # 2. Memory Profiling Example
    print("\n2. Memory Profiling Demo")
    print("-" * 25)
    
    memory_profiler = MemoryProfiler(track_allocations=True)
    
    # Start memory profiling
    memory_profiler.start_profiling()
    
    print("Running memory-intensive operations...")
    
    # Take snapshots during execution
    memory_profiler.take_snapshot()  # Snapshot 1
    
    # Simulate memory usage
    large_data = simulate_memory_intensive_work()
    
    memory_profiler.take_snapshot()  # Snapshot 2
    
    # Create more data
    [large_data[:] for _ in range(5)]
    
    memory_profiler.take_snapshot()  # Snapshot 3
    
    # Stop profiling and get results
    memory_result = memory_profiler.stop_profiling()
    
    print("✅ Memory profiling completed!")
    print(f"   Memory growth: {memory_result.memory_growth:.1f}MB")
    print(f"   Peak memory: {memory_result.peak_memory:.1f}MB")
    print(f"   Potential leaks: {len(memory_result.potential_leaks)}")
    
    if memory_result.potential_leaks:
        print("   Potential leaks:")
        for leak in memory_result.potential_leaks:
            print(f"     - {leak['description']} (Severity: {leak['severity']})")
    
    if memory_result.recommendations:
        print("   Memory recommendations:")
        for rec in memory_result.recommendations[:3]:  # Show first 3
            print(f"     - {rec}")
    
    # 3. Benchmark Runner Example
    print("\n3. Benchmark Runner Demo")
    print("-" * 25)
    
    # Create benchmark runner
    BenchmarkRunner(output_dir="example_benchmark_results")
    
    # Note: This is a demonstration - actual benchmarks would use real config files
    print("Setting up example benchmarks...")
    
    # Create some example benchmark configurations
    [
        BenchmarkConfig(
            name="fast_config",
            config_file="config.yaml",  # Would be actual config file
            benchmark_file="benchmarks/benchmark1_fixed.asm",
            max_cycles=1000,
            enable_profiling=True,
        ),
        BenchmarkConfig(
            name="detailed_config",
            config_file="config.yaml",
            benchmark_file="benchmarks/benchmark3_fibonacci.asm",
            max_cycles=5000,
            enable_profiling=True,
        ),
    ]
    
    print("Note: Benchmark runner requires actual simulator integration")
    print("This example shows the API structure for future implementation")
    
    # Show how benchmarks would be run (commented out since we don't have full integration)
    # results = benchmark_runner.run_benchmarks(benchmarks, parallel=False)
    # benchmark_runner.generate_report("benchmark_report.json")
    # benchmark_runner.generate_html_report("benchmark_report.html")
    
    print("✅ Benchmark runner API demonstrated")
    
    # 4. Save profiling data example
    print("\n4. Saving Profiling Data")
    print("-" * 25)
    
    try:
        # Save detailed profiling data
        profiler.save_profile_data("example_profile.prof")
        print("✅ Detailed profiling data saved to 'example_profile.prof'")
        print("   Use 'python -m pstats example_profile.prof' to analyze")
        
        # Generate memory report
        memory_profiler.generate_memory_report("memory_report.txt")
        print("✅ Memory report saved to 'memory_report.txt'")
        
        # Clean up example files
        Path("example_profile.prof").unlink(missing_ok=True)
        Path("memory_report.txt").unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Error saving profiling data: {e}")
    
    print("\n" + "=" * 40)
    print("Profiling example completed!")
    print("\nKey takeaways:")
    print("- Use PerformanceProfiler for execution time and CPU analysis")
    print("- Use MemoryProfiler for memory usage and leak detection")
    print("- Use BenchmarkRunner for automated performance testing")
    print("- All profilers provide actionable recommendations")


if __name__ == '__main__':
    main()
