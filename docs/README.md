# Superscalar Pipeline Simulator Documentation

---

## Documentation Overview

Welcome to the comprehensive documentation for the Superscalar Pipeline Simulator. This documentation is organized to serve different user needs, from quick start guides to deep technical references.

---

## Getting Started

### For New Users
1. **[Installation Guide](installation.md)** - Step-by-step installation for all platforms
2. **[Quick Start Tutorial](user_guide.md#quick-start)** - Run your first simulation in 5 minutes
3. **[User Guide](user_guide.md)** - Complete guide to using the simulator

### For Developers
1. **[API Reference](api_reference.md)** - Complete API documentation
2. **[Design Document](design_document.md)** - Architecture and implementation details
3. **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to the project

---

## Documentation Structure

### User Documentation
| Document | Description | Audience |
|----------|-------------|----------|
| [Installation Guide](installation.md) | Platform-specific installation instructions | All users |
| [User Guide](user_guide.md) | Complete usage guide with examples | Beginners to Advanced |
| [Configuration Reference](#) | YAML configuration options and parameters | All users |
| [Benchmark Guide](#) | Available benchmarks and how to create custom ones | Researchers |

### Technical Documentation
| Document | Description | Audience |
|----------|-------------|----------|
| [API Reference](api_reference.md) | Complete module and class documentation | Developers |
| [Design Document](design_document.md) | Architecture, algorithms, and design decisions | Researchers, Developers |
| [Pipeline Architecture](#) | Detailed pipeline implementation | Advanced users |
| [Branch Prediction](#) | Branch predictor algorithms and performance | Researchers |

### Development Documentation
| Document | Description | Audience |
|----------|-------------|----------|
| [Contributing Guide](../CONTRIBUTING.md) | How to contribute code and documentation | Contributors |
| [Testing Guide](#) | Testing framework and best practices | Developers |
| [Code Style Guide](#) | Coding standards and conventions | Developers |
| [Release Process](#) | How to create releases | Maintainers |

---

## Key Features

### Core Capabilities
- **6-Stage Superscalar Pipeline**: FETCH → DECODE → ISSUE → EXECUTE → MEMORY → WRITEBACK
- **Out-of-Order Execution**: Reservation stations with register renaming
- **Advanced Branch Prediction**: Tournament, Perceptron, Adaptive Hybrid, GShare, Bimodal
- **Non-Blocking Cache**: MSHR support with up to 8 outstanding misses
- **Data Forwarding**: Multiple bypass paths (EX→EX, MEM→EX, WB→EX)
- **Power Modeling**: Component-level analysis with thermal effects

### Research Tools
- **Cycle-Accurate Simulation**: Precise timing models
- **Performance Profiling**: Bottleneck identification and optimization
- **Memory Analysis**: Cache hit/miss tracking and patterns
- **Energy Metrics**: EPI calculations and power breakdown

---

## Quick Reference

### Command Line Usage
```bash
# Basic simulation
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100

# With configuration file
python main.py --config config.yaml --benchmark benchmarks/matrix_multiplication.asm

# With profiling and visualization
python main.py --benchmark benchmarks/sort.asm --profile --visualize

# Debug mode
python main.py --benchmark benchmarks/test.asm --debug --max-cycles 50
```

### Configuration Example
```yaml
pipeline:
  num_stages: 6
  fetch_width: 4
  issue_width: 4
  execute_units:
    ALU: {count: 4, latency: 1}
    FPU: {count: 2, latency: 3}
    LSU: {count: 2, latency: 2}

branch_predictor:
  type: tournament
  num_entries: 1024
  history_length: 8

memory:
  instruction_cache:
    size: 32KB
    block_size: 64
    associativity: 4
  data_cache:
    size: 32KB
    block_size: 64
    associativity: 4
    mshr_count: 8
```

### Python API Example
```python
from main import SuperscalarSimulator

# Create and run simulator
simulator = SuperscalarSimulator('config.yaml')
simulator.load_program('benchmarks/simple_arithmetic.asm')
results = simulator.run_simulation()

print(f"IPC: {results['ipc']:.3f}")
print(f"Cycles: {results['cycles']}")
```

---

## Available Benchmarks

| Benchmark | Description | Complexity | Best For |
|-----------|-------------|------------|----------|
| `simple_arithmetic.asm` | Basic arithmetic operations (ADD, SUB, AND, OR, XOR) | Simple | Testing, Quick validation |
| `simple_sort.asm` | Simple sorting algorithm | Simple | Control flow analysis |
| `simple_fibonacci.asm` | Iterative Fibonacci | Simple | Loop behavior |
| `simple_test.asm` | Basic test program | Simple | Smoke testing |
| `basic_operations.asm` | Fundamental operations | Medium | General testing |
| `validation_suite.asm` | Comprehensive tests | Medium | Simulator validation |
| `matrix_multiplication.asm` | 4×4 matrix multiply | Complex | Memory access patterns |
| `bubble_sort.asm` | Bubble sort algorithm | Complex | Branch prediction |
| `fibonacci_recursive.asm` | Recursive Fibonacci | Complex | Stack operations |
| `memory_access_patterns.asm` | Various memory patterns | Complex | Cache analysis |
| `integer/dhrystone_like.asm` | Integer-intensive loops & arrays | Complex | Steady-state IPC |
| `integer/quicksort.asm` | Quicksort partitioning | Complex | Branch-heavy workloads |
| `memory/streaming_access.asm` | Sequential & strided access | Complex | Cache behavior |
| `mixed/compute_intensive.asm` | ALU + memory + branches | Complex | Realistic IPC |

---

## Performance Metrics

### Key Metrics Tracked
- **IPC (Instructions Per Cycle)**: Overall throughput
- **Pipeline Utilization**: Per-stage usage percentages
- **Branch Prediction Accuracy**: Prediction success rate
- **Cache Hit Rate**: L1/L2 cache effectiveness
- **Stall Cycles**: Cycles lost to hazards
- **Power Consumption**: Dynamic and static power
- **Energy Per Instruction**: Energy efficiency

### Example Output

![Benchmark Comparison](../artifacts/benchmark_comparison.png)

| Benchmark | IPC | Cycles | Branch Accuracy | Cache Hit Rate | EPI (pJ) |
|-----------|-----|--------|-----------------|----------------|----------|
| basic_operations | 0.620 | 10000 | 95.9% | 99.1% | 104925.4 |
| bubble_sort | 0.923 | 10000 | 100.0% | 99.7% | 80930.7 |
| fibonacci_recursive | 0.833 | 10000 | 96.7% | 80.3% | 87015.1 |
| dhrystone_like | 0.781 | 8043 | 95.9% | 91.0% | 90897.3 |
| quicksort | 0.946 | 10000 | 99.6% | 99.4% | 80525.6 |
| matrix_multiplication | 0.921 | 38 | 0.0% | 0.0% | 80242.3 |
| streaming_access | 0.876 | 10000 | 99.7% | 99.6% | 83988.4 |
| memory_access_patterns | 0.889 | 10000 | 100.0% | 99.6% | 83946.0 |
| compute_intensive | 0.739 | 2881 | 93.6% | 95.0% | 93901.1 |
| simple_arithmetic | 0.604 | 48 | 76.9% | 0.0% | 100287.8 |
| simple_fibonacci | 0.688 | 48 | 66.7% | 0.0% | 94089.1 |
| simple_sort | 0.826 | 23 | 100.0% | 25.0% | 79600.2 |
| simple_test | 0.667 | 9 | 0.0% | 0.0% | 79066.9 |
| validation_suite | 0.826 | 10000 | 99.9% | 99.5% | 88478.3 |

---

## Learning Resources

### For Students
1. Start with [User Guide](user_guide.md) to understand basic concepts
2. Run simple benchmarks to see pipeline behavior
3. Enable visualization to observe instruction flow
4. Experiment with different configurations
5. Study [Design Document](design_document.md) for implementation details

### For Researchers
1. Review [API Reference](api_reference.md) for programmatic access
2. Use profiling tools for detailed analysis
3. Create custom benchmarks for specific scenarios
4. Compare different branch predictors
5. Analyze cache behavior with memory-intensive workloads

### For Educators
1. Use examples in `examples/` directory for demonstrations
2. Start with simple pipelines, gradually add complexity
3. Show impact of different configurations on performance
4. Use visualization tools for classroom demonstrations
5. Assign projects based on extending the simulator

---

## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| Import errors | Run from project root directory |
| Configuration errors | Validate YAML syntax, check [config.yaml](../config.yaml) |
| Benchmark errors | Verify MIPS assembly syntax |
| Performance issues | Reduce max_cycles or use simpler benchmarks |
| GUI errors | Install tkinter: `sudo apt install python3-tk` |

---

## Documentation Standards

All documentation follows these standards:
- **Format**: Markdown (CommonMark compliant)
- **Language**: Clear, concise, technical English
- **Code Examples**: Tested and working
- **Diagrams**: ASCII or Mermaid when helpful
- **Updates**: Synchronized with code changes
- **Review**: Peer-reviewed before merging
