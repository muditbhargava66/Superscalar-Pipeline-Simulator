<div align = "center">

# Superscalar Pipeline Simulator

[![CI/CD Pipeline](https://github.com/muditbhargava66/superscalar-pipeline-simulator/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/muditbhargava66/superscalar-pipeline-simulator/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**A comprehensive, high-performance superscalar pipeline simulator for computer architecture research and education. This simulator provides detailed modeling of modern processor features including out-of-order execution, branch prediction, cache hierarchies, and data forwarding.**

</div>

## 🚀 Features

### Core Pipeline Features
- **Superscalar Execution**: Multiple execution units (ALU, FPU, LSU) with configurable counts
- **Out-of-Order Execution**: Reservation stations and register renaming
- **Advanced Branch Prediction**: Always-taken, bimodal, and GShare predictors
- **Multi-Level Cache**: Configurable instruction and data caches with realistic timing
- **Data Forwarding**: Comprehensive forwarding paths to minimize pipeline stalls
- **Hazard Detection**: RAW, WAR, and WAW hazard detection and resolution

### Advanced Features
- **Performance Profiling**: Built-in execution time and memory usage analysis
- **Pipeline Visualization**: Real-time pipeline state visualization
- **Configuration Management**: Type-safe configuration with validation
- **Error Handling**: Comprehensive exception hierarchy with detailed context
- **Benchmark Suite**: Multiple assembly programs for testing and validation

### Developer Features
- **Modern Python**: Full Python 3.10+ support with type hints
- **Comprehensive Testing**: 76+ test cases with high coverage
- **Documentation**: Extensive documentation with examples
- **CI/CD Ready**: GitHub Actions workflow for automated testing

## 📦 Installation

### Clone and Install

```bash
git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git
cd superscalar-pipeline-simulator
make dev-setup
```

### Manual Installation

```bash
git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git
cd superscalar-pipeline-simulator
pip install -r requirements.txt
```

### Requirements

- Python 3.10 or higher
- Dependencies listed in `requirements.txt`
- Optional: Development dependencies in `requirements-dev.txt`

## 🏃 Quick Start

### Basic Simulation

```bash
# Run a simple matrix multiplication benchmark
python main.py --benchmark benchmarks/benchmark1_matrix_multiplication.asm

# Enable visualization and profiling
python main.py --benchmark benchmarks/benchmark3_fibonacci.asm --visualize --profile

# Custom configuration
python main.py --config config.yaml --benchmark benchmarks/benchmark2_bubble_sort.asm
```

### Python API

```python
# Add the project to your Python path
import sys
sys.path.insert(0, 'path/to/superscalar-pipeline-simulator')

from main import SuperscalarSimulator

# Create and configure simulator
simulator = SuperscalarSimulator('config.yaml')

# Load and run a program
simulator.load_program('benchmarks/benchmark1_matrix_multiplication.asm')
results = simulator.run_simulation()

# Analyze results
print(f"IPC: {results['ipc']:.2f}")
print(f"Branch Accuracy: {results['branch_accuracy']:.1f}%")
```

## 📊 Benchmarks

The simulator includes several benchmark programs:

| Benchmark | Description | Features Tested |
|-----------|-------------|-----------------|
| `benchmark1_matrix_multiplication.asm` | 4x4 matrix multiplication | ALU operations, memory access patterns |
| `benchmark2_bubble_sort.asm` | Bubble sort algorithm | Branch prediction, data dependencies |
| `benchmark3_fibonacci.asm` | Recursive Fibonacci | Function calls, stack operations |
| `benchmark4_memory_patterns.asm` | Memory access patterns | Cache behavior, memory hierarchy |

## ⚙️ Configuration

### Basic Configuration

```yaml
pipeline:
  num_stages: 6
  fetch_width: 4
  issue_width: 4
  execute_units:
    ALU:
      count: 2
      latency: 1
    FPU:
      count: 1
      latency: 3
    LSU:
      count: 1
      latency: 2

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
```

### Environment Variables

```bash
export SIMULATOR_PIPELINE__FETCH_WIDTH=8
export SIMULATOR_DEBUG__ENABLED=true
python main.py --benchmark benchmarks/benchmark1_matrix_multiplication.asm
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
python -m pytest tests/test_branch_prediction.py -v
python -m pytest tests/test_enhanced_features.py -v

# Run with coverage
make test
```

## 📈 Performance Analysis

The simulator provides comprehensive performance analysis:

```bash
# Enable profiling
python main.py --benchmark benchmarks/benchmark1_matrix_multiplication.asm --profile

# Memory profiling
python main.py --benchmark benchmarks/benchmark4_memory_patterns.asm --profile --debug
```

### Sample Output

```
Simulation Summary:
  Cycles: 1000
  Instructions: 100
  IPC: 0.100
  Branch Accuracy: 92.0%
  Cache Hit Rate: 95.2%
  
Performance Profile:
  Execution Time: 0.045s
  Memory Growth: 2.3MB
  Bottlenecks: 2 identified
```

## 🏗️ Architecture

The simulator is built with a modular architecture:

```
src/
├── pipeline/           # Pipeline stage implementations
├── branch_prediction/  # Branch predictor algorithms
├── cache/             # Cache and memory system
├── utils/             # Utility components
├── config/            # Configuration management
├── exceptions/        # Error handling
├── profiling/         # Performance analysis
└── gui/              # Graphical interface
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

```bash
# Set up development environment
make dev-setup

# Make changes and test
make dev

# Run full test suite
make ci-test

# Submit pull request
```

## 📚 Documentation

- **[User Guide](docs/user_guide.md)**: Complete usage instructions
- **[Installation Guide](docs/installation.md)**: Detailed installation instructions
- **[API Reference](docs/api_reference.md)**: Complete API documentation
- **[Architecture Guide](docs/architecture.md)**: System design and implementation
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

## 🐛 Issues and Support

- **Bug Reports**: [GitHub Issues](https://github.com/muditbhargava66/superscalar-pipeline-simulator/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/muditbhargava66/superscalar-pipeline-simulator/issues)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Computer architecture research community
- Open source contributors
- Educational institutions using this simulator

---

**Made with ❤️ for computer architecture education and research**