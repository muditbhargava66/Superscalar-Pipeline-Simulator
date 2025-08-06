# User Guide

## Quick Start

The Superscalar Pipeline Simulator is a comprehensive tool for simulating and analyzing superscalar processor architectures. This guide will help you get started quickly.

### Basic Usage

1. **Run a simple simulation:**
   ```bash
   python main.py --config config.yaml --benchmark benchmarks/benchmark1_matrix_multiplication.asm
   ```

2. **Enable visualization:**
   ```bash
   python main.py --config config.yaml --benchmark benchmarks/benchmark3_fibonacci.asm --visualize
   ```

3. **Generate performance report:**
   ```bash
   python main.py --config config.yaml --benchmark benchmarks/benchmark4_memory_patterns.asm --profile
   ```

### Using the GUI Configuration Tool

For easier configuration management, use the GUI tool:

```bash
python -c "import sys; sys.path.insert(0, 'src'); from gui.config_gui import main; main()"
```

The GUI provides:
- Pipeline parameter configuration
- Branch predictor settings
- Cache configuration
- Simulation options
- Load/save configuration files

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

branch_predictor:
  type: gshare
  num_entries: 1024
  history_length: 8

cache:
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

### Branch Predictor Options

- **always_taken**: Simple predictor that always predicts taken
- **bimodal**: Two-bit saturating counter predictor
- **gshare**: Global history with shared pattern history table

### Cache Configuration

- **size**: Cache size in bytes
- **block_size**: Cache block size in bytes
- **associativity**: Number of ways (1 = direct mapped)

## Benchmarks

### Available Benchmarks

1. **benchmark1_matrix_multiplication.asm**: Matrix multiplication (4x4)
2. **benchmark2_bubble_sort.asm**: Bubble sort algorithm
3. **benchmark3_fibonacci.asm**: Recursive Fibonacci calculation
4. **benchmark4_memory_patterns.asm**: Memory access patterns

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

### Performance Metrics

- **IPC (Instructions Per Cycle)**: Overall performance measure
- **Branch Prediction Accuracy**: Percentage of correct predictions
- **Cache Hit Rate**: Percentage of cache hits
- **Pipeline Stalls**: Cycles lost to hazards

### Visualization

When visualization is enabled, you'll see:

- Pipeline stage utilization over time
- Instruction flow through stages
- Hazard detection and resolution
- Performance trends

## Advanced Usage

### Enhanced Command Line Interface

The simulator now includes an enhanced command-line interface with comprehensive options:

```bash
python main.py [options]

Configuration Options:
  --config, -c CONFIG           Configuration file (default: config.yaml)
  --generate-config FILE        Generate example configuration file
  --validate-config FILE        Validate configuration file

Simulation Options:
  --benchmark, -b BENCH         Benchmark file to run
  --output, -o OUTPUT           Output file for results
  --visualize                   Enable pipeline visualization

Profiling Options:
  --profile                     Enable performance profiling
  --memory-profile              Enable memory profiling

Debug Options:
  --debug                       Enable debug mode
  --log-level LEVEL             Set logging level (DEBUG, INFO, WARNING, ERROR)
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

### Batch Processing

Run multiple benchmarks:

```bash
#!/bin/bash
for benchmark in benchmarks/*.asm; do
    echo "Running $benchmark"
    python main.py --config config.yaml --benchmark "$benchmark" --output "results/$(basename $benchmark .asm).txt"
done
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

- Explore [Advanced Configuration](configuration.md)
- Try [Tutorial Examples](tutorials/)
- Read [Architecture Documentation](architecture.md)
- Contribute to the project (see [Contributing Guide](contributing.md))