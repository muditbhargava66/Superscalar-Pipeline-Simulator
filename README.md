<div align="center">

# Superscalar Pipeline Simulator

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/muditbhargava66/superscalar-pipeline-simulator/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-139%20passing-green.svg)](https://github.com/muditbhargava66/superscalar-pipeline-simulator)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-brightgreen.svg)](docs/)

> Superscalar pipeline simulator for computer architecture research and education. Features branch prediction, non-blocking cache systems, power modeling, and cycle-accurate simulation capabilities.

**[Quick Start](#quick-start)** • **[Get Started Now](docs/installation.md)** • **[View Examples](examples/)** • **[Benchmarks](#benchmarks)** • **[![Star this repository](https://img.shields.io/github/stars/muditbhargava66/superscalar-pipeline-simulator?style=social)](https://github.com/muditbhargava66/superscalar-pipeline-simulator)**

</div>

## Features

<table>
<tr>
<td width="50%">

### Research Platform
- **6 Branch Predictors** - Always Taken, Bimodal, GShare, Tournament, Perceptron, Adaptive Hybrid
- **Non-blocking Cache System** - MSHR-based with up to 8 outstanding misses
- **Enhanced Register Renaming** - 64-entry ROB with configurable bandwidth (4/cycle)
- **Power & Energy Modeling** - Component-level analysis with thermal effects
- **Error Handling** - Structured exceptions with recovery guidance

### Core Architecture
- **Superscalar Execution** - Multiple ALU/FPU/LSU units with configurable counts
- **Out-of-Order Execution** - Advanced reservation stations and register renaming
- **Multi-Level Cache Hierarchy** - Realistic L1I/L1D/L2 with configurable parameters
- **Data Forwarding** - Comprehensive bypass paths minimizing pipeline stalls
- **Hazard Detection** - Complete RAW/WAR/WAW hazard resolution

</td>
<td width="50%">

### Development Tools
- **Complete Example Suite** - 5 demonstrations of all features
- **Working Benchmark Suite** - 14 tested assembly programs for evaluation
- **Type-Safe Configuration** - Pydantic validation with environment overrides
- **Modern Python API** - Full 3.10+ compatibility with comprehensive type hints
- **Documentation** - API reference, guides, and tutorials

### Capabilities
- **Performance Analysis** - Bottleneck identification and optimization recommendations
- **Cycle-Accurate Simulation** - Precise timing models for analysis
- **Live Visualization** - Real-time pipeline state display with matplotlib
- **Configuration GUI** - Tkinter-based interactive config editor
- **Machine Learning Integration** - Advanced predictors with adaptive algorithms

</td>
</tr>
</table>

## Quick Start

### One-Line Installation

```bash
git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git && cd superscalar-pipeline-simulator && pip install -r requirements.txt
```

### First Simulation

```bash
# Run a simple benchmark
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100

# Run with live visualization
python main.py --benchmark benchmarks/simple_fibonacci.asm --visualize --max-cycles 200

# Launch the configuration GUI
make run-gui
# Or manually: python main.py --gui --benchmark benchmarks/simple_arithmetic.asm

# Try advanced features
python examples/advanced_pipeline_features.py

# Explore power modeling
python examples/performance_analysis.py
```

## Usage Examples

### Basic Simulation
```bash
# Simple arithmetic benchmark
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100

# Complex sorting algorithm
python main.py --benchmark benchmarks/bubble_sort.asm --max-cycles 200 --profile

# Recursive function calls
python main.py --benchmark benchmarks/fibonacci_recursive.asm --max-cycles 200

# Run with debug output
python main.py --benchmark benchmarks/matrix_multiplication.asm --debug --max-cycles 300
```

### Advanced Analysis
```bash
# Power consumption analysis
python examples/performance_analysis.py

# Branch prediction evaluation
python examples/advanced_pipeline_features.py

# Configuration management
python examples/configuration_management.py
```

### Python API
```python
from src.config.config_manager import ConfigManager
from src.utils.execution_engine import CycleAccurateExecutionEngine

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_default()

# Create simulator
from main import SuperscalarSimulator
simulator = SuperscalarSimulator()

# Load and run a program
simulator.load_program("benchmarks/simple_arithmetic.asm")
results = simulator.run_simulation()

# Analyze results
print(f"IPC: {results['ipc']:.3f}")
print(f"Branch Accuracy: {results['branch_accuracy']:.1f}%")
```

## Benchmarks

<div align="center">

### Comprehensive Benchmark Suite

</div>

<table>
<tr>
<th width="25%">Simple Benchmarks</th>
<th width="25%">Complex Benchmarks</th>
<th width="25%">Research Benchmarks</th>
<th width="25%">Validation Suite</th>
</tr>
<tr>
<td>

**simple_arithmetic.asm**
- Basic operations
- Control flow
- Pipeline testing

**simple_sort.asm**
- Array sorting
- Comparisons
- Branch patterns

**simple_fibonacci.asm**
- Iterative calculation
- Loop optimization
- Register usage

</td>
<td>

**bubble_sort.asm**
- Nested loops
- Memory access patterns
- Branch prediction stress

**fibonacci_recursive.asm**
- Function calls
- Stack management
- Return address handling

**matrix_multiplication.asm**
- 4x4 matrix operations
- Complex addressing
- ALU intensive workload

</td>
<td>

**memory_access_patterns.asm**
- Sequential access
- Strided patterns
- Cache evaluation

**basic_operations.asm**
- Comprehensive ISA testing
- Pipeline hazards
- Resource conflicts

</td>
<td>

**validation_suite.asm**
- Complete functionality
- Edge case testing
- Error condition handling

**Performance Testing**
- Bottleneck identification
- Optimization validation
- Regression testing

</td>
</tr>
</table>

### Performance Metrics

![Benchmark Comparison](artifacts/benchmark_comparison.png)

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

### Extended Benchmarks

Additional benchmarks in subdirectories for advanced workload testing:

| Benchmark | Category | Description | Instructions |
|-----------|----------|-------------|--------------|
| `integer/dhrystone_like.asm` | Integer | Integer-intensive loops, arrays, string-like ops | ~200 |
| `integer/quicksort.asm` | Integer | Quicksort partitioning, branch-heavy workload | ~150 |
| `memory/streaming_access.asm` | Memory | Sequential, strided, random-like access patterns | ~120 |
| `mixed/compute_intensive.asm` | Mixed | ALU + memory + branches, scientific computation | ~300 |

```bash
# Run extended benchmarks
python main.py --benchmark benchmarks/integer/dhrystone_like.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/integer/quicksort.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/memory/streaming_access.asm --max-cycles 200 --profile
python main.py --benchmark benchmarks/mixed/compute_intensive.asm --max-cycles 300 --profile
```

## Configuration

### Pipeline Configuration
```python
pipeline_config = {
    'fetch_width': 4,        # Instructions per cycle
    'issue_width': 4,        # Issue queue width
    'num_stages': 6,         # Pipeline depth
    'execution_units': {
        'ALU': {'count': 2, 'latency': 1},
        'FPU': {'count': 1, 'latency': 4},
        'LSU': {'count': 1, 'latency': 2}
    }
}
```

### Branch Prediction
```python
branch_config = {
    'type': 'tournament',    # tournament, perceptron, gshare
    'num_entries': 2048,     # Predictor table size
    'history_length': 16,    # Global history length
    'meta_bits': 10          # Meta-predictor size
}
```

### Memory Hierarchy
```python
memory_config = {
    'instruction_cache': {
        'size': 32768,       # 32KB L1I cache
        'associativity': 4,  # 4-way set associative
        'block_size': 64     # 64-byte cache lines
    },
    'data_cache': {
        'size': 32768,       # 32KB L1D cache
        'associativity': 4,
        'mshr_count': 8      # Outstanding misses
    },
    'l2_cache': {
        'size': 262144,      # 256KB L2 cache
        'associativity': 8
    }
}
```

### Power Modeling
```python
power_config = {
    'technology_nm': 45.0,   # Process technology
    'voltage_v': 1.0,        # Supply voltage
    'frequency_ghz': 2.5,    # Operating frequency
    'temperature_k': 350     # Operating temperature
}
```

### Environment Variables
```bash
# Pipeline configuration
export SIMULATOR_PIPELINE__FETCH_WIDTH=8
export SIMULATOR_PIPELINE__ISSUE_WIDTH=6

# Debug and profiling
export SIMULATOR_DEBUG__ENABLED=true
export SIMULATOR_PROFILING__DETAILED=true

# Power modeling
export SIMULATOR_POWER__TECHNOLOGY_NM=32
```

## Performance Analysis

### Comprehensive Profiling
```bash
# Basic performance analysis
python main.py --benchmark benchmarks/bubble_sort.asm --profile

# Detailed power analysis
python examples/performance_analysis.py

# Memory usage profiling
python examples/error_handling_showcase.py
```

### Sample Output
```
Simulation Results:
==========================================
Execution Metrics:
  Cycles: 1,250
  Instructions: 856
  IPC: 0.685

Performance Analysis:
  Branch Accuracy: 94.2%
  L1 Cache Hit Rate: 96.8%
  L2 Cache Hit Rate: 89.3%

Power Consumption:
  Average Power: 12.4W
  Total Energy: 15.5mJ
  Energy per Instruction: 18.1µJ

Bottlenecks Identified:
  1. Branch misprediction penalty: 8.3%
  2. Cache miss latency: 5.7%
  3. Resource conflicts: 3.2%
```

### Testing Framework
```bash
# Run complete test suite
python -m pytest tests/ -v --cov=src

# Test specific components
python -m pytest tests/test_branch_prediction.py
python -m pytest tests/test_pipeline.py
python -m pytest tests/test_pipeline_enhancements.py

# Performance regression tests
python -m pytest tests/test_complete_pipeline.py --benchmark

# Quick test (no coverage)
python -m pytest tests/ --no-cov -q
```

### Quality Metrics
- **Test Coverage**: 139 tests with comprehensive validation
- **Code Quality**: Ruff linting and formatting (replaces black, isort, flake8)
- **Type Safety**: MyPy validation with strict mode
- **Documentation**: Comprehensive API coverage
- **Performance**: Benchmarked against reference implementations
- **Pre-commit Hooks**: Automated code quality checks before commits

## Architecture

<div align="center">

### Modular Design Philosophy

<table>
<tr>
<td width="33%">

### Core Pipeline
```
src/pipeline/
├── fetch_stage.py
├── decode_stage.py
├── execute_stage.py
├── issue_stage.py
├── memory_access_stage.py
├── write_back_stage.py
└── hazard_controller.py
```

**Features:**
- Superscalar execution
- Out-of-order processing
- Hazard detection
- Data forwarding

</td>
<td width="33%">

### Prediction & Memory
```
src/branch_prediction/
├── always_taken_predictor.py
├── bimodal_predictor.py
├── gshare_predictor.py
└── hybrid_predictor.py

src/cache/
├── cache.py
├── enhanced_cache.py
└── non_blocking_cache.py
```

**Features:**
- Advanced branch prediction
- MSHR-based caches
- Multi-level hierarchy
- Realistic timing models

</td>
<td width="33%">

### Support Systems
```
src/config/
├── config_manager.py
└── config_models.py

src/profiling/
├── power_model.py
├── performance_profiler.py
└── memory_profiler.py

src/exceptions/
└── simulator_exceptions.py
```

**Features:**
- Type-safe configuration
- Comprehensive profiling
- Professional error handling
- Extensible design

</td>
</tr>
</table>
</div>
