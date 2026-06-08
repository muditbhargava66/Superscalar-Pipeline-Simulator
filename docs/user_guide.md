# User Guide

## Quick Start

The Superscalar Pipeline Simulator is a comprehensive tool for simulating and analyzing superscalar processor architectures. This guide will help you get started quickly.

### Basic Usage

1. **Run a simple simulation:**
   ```bash
   python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100
   ```

2. **Run with different benchmarks:**
   ```bash
   python main.py --benchmark benchmarks/simple_sort.asm --max-cycles 100
   python main.py --benchmark benchmarks/simple_fibonacci.asm --max-cycles 100
   ```

3. **Generate performance report:**
   ```bash
   python main.py --benchmark benchmarks/basic_operations.asm --max-cycles 200 --profile
   ```

### Using the GUI Configuration Tool

For easier configuration management, use the GUI tool:

```bash
# Launch the GUI directly
python main.py --gui

# Or with a pre-selected benchmark
python main.py --gui --benchmark benchmarks/simple_arithmetic.asm

# Alternative: launch the GUI module directly
python -c "import sys; sys.path.insert(0, 'src'); from gui.config_gui import main; main()"
```

The GUI provides:
- Pipeline parameter configuration
- Branch predictor settings
- Cache configuration
- Simulation options
- Load/save configuration files
- **Run simulations directly** from the GUI with results displayed in a scrollable window

## Configuration

### Configuration File Structure

The simulator uses YAML configuration files. Here's the basic structure:

```yaml
pipeline:
  num_stages: 6
  fetch_width: 4
  issue_width: 4
  execute_units:
    ALU:
      count: 2
    FPU:
      count: 1
    LSU:
      count: 1

execution:
  enhanced_renaming: true
  rename_bandwidth: 4
  commit_bandwidth: 4
  ooo_execution: false
  ooo_window_size: 16

branch_predictor:
  type: tournament
  num_entries: 1024
  history_length: 8

memory:
  instruction_cache:
    size: 32768
    block_size: 64
    associativity: 4
  data_cache:
    size: 32768
    block_size: 64
    associativity: 4
  memory_size: 1048576

simulation:
  max_cycles: 10000
  output_file: simulation_results.txt
  enable_visualization: false
  enable_profiling: true

debug:
  enabled: false
  log_level: INFO
```

### Pipeline Configuration

- **num_stages**: Number of pipeline stages (typically 5-6)
- **fetch_width**: Instructions fetched per cycle
- **issue_width**: Instructions issued per cycle
- **execute_units**: Number of each type of execution unit

### Execution Configuration

- **enhanced_renaming**: Enable advanced register renaming with reorder buffer
- **rename_bandwidth**: Max instructions to rename per cycle (default 4)
- **commit_bandwidth**: Max instructions to commit per cycle (default 4)
- **ooo_execution**: Enable out-of-order execution in the execute stage
- **ooo_window_size**: Instruction window size for OOO execution (default 16)

### Branch Predictor Options

- **always_taken**: Simple predictor that always predicts taken
- **bimodal**: Two-bit saturating counter predictor indexed by branch PC
- **gshare**: Global history XOR with branch address for pattern-based prediction
- **tournament**: Meta-predictor chooses between Bimodal and GShare sub-predictors
- **perceptron**: Neural network-based predictor using global history weights
- **adaptive**: Dynamic switching between Tournament and Perceptron based on accuracy

### Cache Configuration

- **size**: Cache size in bytes
- **block_size**: Cache block size in bytes
- **associativity**: Number of ways (1 = direct mapped)

## Benchmarks

### Available Benchmarks

#### Simple Benchmarks (Recommended for Testing)

1. **simple_arithmetic.asm**: Basic arithmetic operations (ADD, SUB, AND, OR, XOR) and control flow
2. **simple_sort.asm**: Simple sorting algorithm with comparisons and swaps
3. **simple_fibonacci.asm**: Iterative Fibonacci calculation
4. **simple_test.asm**: Basic test program for smoke testing

#### Medium Complexity Benchmarks

5. **basic_operations.asm**: Fundamental processor operations and control flow
6. **validation_suite.asm**: Comprehensive test suite for simulator validation

#### Complex / Legacy Benchmarks

7. **matrix_multiplication.asm**: 4×4 matrix multiplication (requires parser enhancements)
8. **bubble_sort.asm**: Bubble sort algorithm (branch-heavy workload)
9. **fibonacci_recursive.asm**: Recursive Fibonacci (stack operations)
10. **memory_access_patterns.asm**: Various memory access patterns for cache analysis

#### Integer Benchmarks (`benchmarks/integer/`)

11. **integer/dhrystone_like.asm**: Integer-intensive workload with loops, arrays, and string-like ops (~200 instructions for steady-state IPC measurement)
12. **integer/quicksort.asm**: Quicksort-like partitioning with branch-heavy workload (~150 instructions)

#### Memory Benchmarks (`benchmarks/memory/`)

13. **memory/streaming_access.asm**: Sequential, strided, and random-like memory access patterns for cache behavior measurement (~120 instructions)

#### Mixed Benchmarks (`benchmarks/mixed/`)

14. **mixed/compute_intensive.asm**: Mixes ALU, memory, and branch operations for realistic IPC measurement simulating scientific computation (~300 instructions)

### Creating Custom Benchmarks

Benchmarks are written in MIPS assembly language:

```assembly
# Example benchmark
.data
test_var: .word 42

.text
.globl main

main:
    li $t0, 10
    li $t1, 20
    add $t2, $t0, $t1
    li $v0, 10
    syscall
```

### Benchmark Guidelines

- Use `.globl main` to define the entry point
- End with `syscall` to terminate
- Use meaningful comments
- Test different instruction types
- Consider cache behavior

## Output and Analysis

### Simulation Output

The simulator generates detailed output including:

- Execution statistics
- Pipeline utilization
- Branch prediction accuracy
- Cache hit/miss rates
- Performance metrics

### Performance Metrics & Physics
The simulator strictly tracks performance using cycle-accurate temporal locality and hazard modeling.

- **IPC (Instructions Per Cycle)**: Overall performance measure, capped at issue width.
- **Branch Prediction Accuracy**: Tracks "warmup" physics. Short tests (e.g., 7 cycles) correctly yield 0.0% accuracy because the predictor hasn't accumulated history.
- **Cache Hit Rate**: L1/L2 hits. Programs bypassing memory (registers only) yield 0.0%. Sequential memory accesses also yield low hit rates unless loop-back reuse occurs, warming the cache.
- **Pipeline Stalls Breakdown**: The total penalty tracked natively across Structural, Data (RAW/WAR/WAW), Control (flushes), and Cache Misses. Visualized dynamically as a Stacked Bar Chart by the benchmark runner.

### Visualization

When visualization is enabled, you'll see:

- Pipeline stage utilization over time
- Instruction flow through stages
- Hazard detection and resolution
- Performance trends

## Advanced Usage

### Enhanced Command Line Interface

The simulator includes the following command-line options:

```bash
python main.py [options]

Configuration Options:
  --config, -c CONFIG           Configuration file (YAML)

Simulation Options:
  --benchmark, -b BENCH         Benchmark file to run (required)
  --output, -o OUTPUT           Output file for results
  --visualize                   Enable pipeline visualization
  --gui                         Launch configuration GUI

Profiling Options:
  --profile                     Enable performance profiling

Debug Options:
  --debug                       Enable debug mode
  --max-cycles N                Maximum simulation cycles
```

### Enhanced Configuration Management

The simulator now uses Pydantic for robust configuration validation:

```python
from config import ConfigManager, SimulatorConfig

# Load and validate configuration
config_manager = ConfigManager()
config = config_manager.load_from_file('config.yaml')

# Environment variable overrides
# SIMULATOR_PIPELINE__FETCH_WIDTH=8
# SIMULATOR_DEBUG__ENABLED=true

# Programmatic configuration updates
config_manager.update_config({
    'pipeline': {'issue_width': 6},
    'simulation': {'max_cycles': 50000}
})
```

### Performance Profiling

Comprehensive performance analysis with bottleneck identification:

```python
from profiling import PerformanceProfiler, MemoryProfiler

# Performance profiling
profiler = PerformanceProfiler()
with profiler.profile_simulation() as session:
    # Run simulation
    results = simulator.run()

profile_result = session.get_results()
print(f"Execution time: {profile_result.execution_time:.3f}s")
print(f"Bottlenecks: {len(profile_result.bottlenecks)}")
for rec in profile_result.recommendations:
    print(f"- {rec}")
```

### Error Handling

Structured error handling with detailed context:

```python
from exceptions import SimulatorError, handle_simulator_error

try:
    simulator.run()
except SimulatorError as e:
    error_info = handle_simulator_error(e, logger)
    print(f"Error: {error_info['message']}")
    print(f"Details: {error_info['details']}")
```

### Development Tools

The project uses modern Python development tools:

**Code Quality:**
- **Ruff**: Fast linting and formatting (replaces black, isort, flake8)
  ```bash
  # Check code quality
  ruff check src/ tests/

  # Format code
  ruff format src/ tests/
  ```

- **MyPy**: Static type checking
  ```bash
  # Type check
  mypy src/ --ignore-missing-imports
  ```

- **Pre-commit**: Automated hooks before commits
  ```bash
  # Install hooks
  pre-commit install

  # Run manually
  pre-commit run --all-files
  ```

### Batch Processing

Run multiple benchmarks:

```bash
#!/bin/bash
for benchmark in benchmarks/*.asm; do
    echo "Running $benchmark"
    python main.py --config config.yaml --benchmark "$benchmark" --output "results/$(basename $benchmark .asm).txt"
done
```

### Example Usage

Run the examples to learn different aspects of the simulator:

```bash
# Basic simulation concepts
python examples/basic_simulation.py

# Advanced processor features
python examples/advanced_pipeline_features.py

# Configuration management
python examples/configuration_management.py

# Performance analysis
python examples/performance_analysis.py

# Error handling
python examples/error_handling_showcase.py
```

### Working Benchmarks

The following benchmarks are tested and working with the current simulator:

```bash
# Simple benchmarks (recommended for testing)
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100
python main.py --benchmark benchmarks/simple_sort.asm --max-cycles 100
python main.py --benchmark benchmarks/simple_fibonacci.asm --max-cycles 100
python main.py --benchmark benchmarks/simple_test.asm --max-cycles 100

# Complex benchmarks (advanced functionality)
python main.py --benchmark benchmarks/basic_operations.asm --max-cycles 200
python main.py --benchmark benchmarks/validation_suite.asm --max-cycles 100

# Research-grade benchmarks (comprehensive testing)
python main.py --benchmark benchmarks/bubble_sort.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/fibonacci_recursive.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/matrix_multiplication.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/memory_access_patterns.asm --max-cycles 200 --profile

# Subdirectory benchmarks (advanced workloads)
python main.py --benchmark benchmarks/integer/dhrystone_like.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/integer/quicksort.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/memory/streaming_access.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/mixed/compute_intensive.asm --max-cycles 300 --profile
```

### Performance Analysis

For detailed performance analysis:

```bash
# Generate comprehensive report
python main.py --config config.yaml --benchmark benchmarks/benchmark4_memory_patterns.asm --profile --output performance_report.json

# Analyze results
python -c "
import json
with open('performance_report.json') as f:
    data = json.load(f)
print(f'IPC: {data[\"ipc\"]:.2f}')
print(f'Branch Accuracy: {data[\"branch_accuracy\"]:.1f}%')
print(f'Cache Hit Rate: {data[\"cache_hit_rate\"]:.1f}%')
"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the project root directory
2. **Configuration Errors**: Validate YAML syntax
3. **Benchmark Errors**: Check assembly syntax
4. **Memory Issues**: Increase memory size in configuration
5. **Performance Issues**: Reduce max_cycles or benchmark complexity

### Debug Mode

Enable debug mode for detailed logging:

```bash
python main.py --config config.yaml --benchmark benchmarks/benchmark1_matrix_multiplication.asm --debug
```

### Getting Help

- Check the [Installation Guide](installation.md)
- Review [API Reference](api_reference.md)
- See [Examples](examples/)
- Open an issue on GitHub

## Best Practices

### Code Quality

- **Use Pre-commit Hooks**: Install with `pre-commit install` to automatically check code before commits
- **Run Ruff Regularly**: `ruff check src/ tests/` to catch issues early
- **Type Check**: `mypy src/ --ignore-missing-imports` to ensure type safety
- **Format Consistently**: `ruff format src/ tests/` to maintain consistent style

### Configuration

- Start with default configuration
- Modify one parameter at a time
- Document configuration changes
- Use meaningful output filenames

### Benchmarking

- Test with multiple benchmarks
- Vary input sizes
- Consider different instruction mixes
- Analyze cache behavior

### Performance Analysis

- Compare different configurations
- Look for bottlenecks
- Consider trade-offs
- Validate results with theory

## Next Steps

- Try [Tutorial Examples](../examples/)
- Read [Architecture Documentation](design_document.md)
- Learn about [Code Quality Tools](#development-tools)
- Contribute to the project (see [Contributing Guide](../CONTRIBUTING.md))
