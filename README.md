<div align="center">

# Superscalar Pipeline Simulator

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/muditbhargava66/superscalar-pipeline-simulator/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-92%20passing-green.svg)](https://github.com/muditbhargava66/superscalar-pipeline-simulator)
[![Documentation](https://img.shields.io/badge/docs-comprehensive-brightgreen.svg)](docs/)

> Superscalar pipeline simulator for computer architecture research and education. Features branch prediction, non-blocking cache systems, power modeling, and cycle-accurate simulation capabilities.

**[Quick Start](#quick-start)** • **[Get Started Now](docs/installation.md)** • **[View Examples](examples/)** • **[Benchmarks](#benchmarks)** • **[![Star this repository](https://img.shields.io/github/stars/muditbhargava66/superscalar-pipeline-simulator?style=social)](https://github.com/muditbhargava66/superscalar-pipeline-simulator)**

</div>

## Features

<table>
<tr>
<td width="50%">

### Research Platform
- **Tournament Branch Prediction** - Hybrid predictors achieving >95% accuracy
- **Non-blocking Cache System** - MSHR-based with up to 8 outstanding misses
- **Enhanced Register Renaming** - 64-entry ROB with precise exception handling
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
- **Working Benchmark Suite** - 9 tested assembly programs for evaluation
- **Type-Safe Configuration** - Pydantic validation with environment overrides
- **Modern Python API** - Full 3.10+ compatibility with comprehensive type hints
- **Documentation** - API reference, guides, and tutorials

### Capabilities
- **Performance Analysis** - Bottleneck identification and optimization recommendations
- **Cycle-Accurate Simulation** - Precise timing models for analysis
- **Thermal Modeling** - Temperature-aware simulation with leakage scaling
- **Energy Efficiency Metrics** - EPI calculations and power breakdown analysis
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
from config.config_manager import ConfigManager
from simulator.enhanced_simulator import EnhancedSimulator

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_default()

# Create simulator
simulator = EnhancedSimulator(config)

# Run simulation
results = simulator.run_program(
    "benchmarks/simple_arithmetic.asm",
    max_cycles=1000
)

# Analyze results
print(f"IPC: {results.ipc:.3f}")
print(f"Power: {results.average_power:.2f}W")
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

| Metric | Simple Benchmarks | Complex Benchmarks | Research Benchmarks |
|--------|-------------------|-------------------|-------------------|
| **IPC** | 0.8 - 1.2 | 0.4 - 0.8 | 0.2 - 0.6 |
| **Branch Accuracy** | >90% | 85-95% | 80-90% |
| **Cache Hit Rate** | >95% | 90-95% | 85-92% |
| **Power Efficiency** | High | Medium | Variable |

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
python -m pytest tests/test_advanced_features.py
python -m pytest tests/test_pipeline.py

# Performance regression tests
python -m pytest tests/test_complete_pipeline.py --benchmark
```

### Quality Metrics
- **Test Coverage**: 92 tests with comprehensive validation
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
├── memory_stage.py
├── writeback_stage.py
└── pipeline_controller.py
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
├── tournament_predictor.py
├── perceptron_predictor.py
└── hybrid_predictor.py

src/cache/
├── non_blocking_cache.py
├── enhanced_cache.py
└── memory_hierarchy.py
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
└── validation.py

src/profiling/
├── power_model.py
├── performance_profiler.py
└── bottleneck_analyzer.py

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