# Changelog

All notable changes to the Superscalar Pipeline Simulator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-01

### Major Features - Advanced Research Platform
- **Enhanced Branch Prediction**: Tournament, Perceptron, and Adaptive Hybrid predictors with >95% accuracy.
- **Non-blocking Cache Support**: MSHR-based cache with speculative load support and up to 8 outstanding misses.
- **Enhanced Register Renaming**: Deep reorder buffer (64 entries) with improved out-of-order execution.
- **Power and Energy Modeling**: Complete processor power model with dynamic/static power estimation and thermal analysis.
- **Energy Efficiency Metrics**: Energy Per Instruction (EPI), power breakdown by component, MIPS/W calculations.
- **Thermal Modeling**: Temperature-aware simulation with leakage scaling and thermal throttling.
- **Advanced Hazard Resolution**: Improved RAW/WAR/WAW hazard detection and resolution.
- **Dynamic Voltage/Frequency Scaling**: DVFS support for power management research.
- **Clock and Power Gating**: Fine-grained power management capabilities.

### Codebase Stability & Bug Fixes
- **Pipeline Advancement Fix**: Resolved a critical pipeline loop issue that prevented instructions from advancing properly. This resulted in a 3.5x IPC improvement.
- **Dynamic Pipeline Statistics**: Removed hardcoded utilization statistics and replaced them with accurate, dynamically calculated values based on hazard controller metrics.
- **Import and Typing Standardization**: Corrected inconsistent import paths, eliminated circular dependencies, and enforced strict typing standards across the repository.
- **Example Fixes**: Corrected missing OS imports and outdated benchmark file references within example scripts.

### Development Tools & Workflow
- **Linter & Formatter Migration**: Replaced Black, Isort, and Flake8 with Ruff for unified, significantly faster code linting and formatting.
- **Static Type Checking**: Integrated MyPy for rigorous type validation across all core modules.
- **Pre-commit Hooks**: Established a `.pre-commit-config.yaml` to run Ruff, MyPy, and various structural checks automatically before commits.
- **CI/CD Pipeline**: Upgraded GitHub Actions configurations to use modern action versions, validating builds against Ubuntu and macOS across Python 3.10-3.12.

### Testing & Verification
- **Test Suite Restructuring**: Consolidated version-specific test files into unified, comprehensive test modules (e.g., `test_advanced_features.py`).
- **Full Verification**: The test suite now includes 92 tests with a 100% pass rate.
- **Configuration Management**: Streamlined `pyproject.toml` and deduplicated `requirements.txt` dependencies, updating to modern ecosystem constraints.

### Documentation & Analysis
- **Theoretical vs Actual Analysis**: Conducted a deep dive on implementation gaps compared to real-world processors, providing a long-term improvement roadmap.
- **Documentation Restructuring**: Updated user guides, API references, and installation instructions to reflect the new tooling and usage patterns.

## [1.0.0] - 2025-08-06

### Added - Initial Production Release
- Complete superscalar pipeline simulator implementation
- Support for multiple execution units (ALU, FPU, LSU)
- Basic branch prediction algorithms (Always Taken, Bimodal, GShare)
- Multi-level cache hierarchy with configurable parameters
- Data forwarding and hazard detection
- Out-of-order execution with reservation stations
- Register renaming and scoreboard implementation
- Performance profiling and analysis tools
- Memory usage tracking and leak detection
- Comprehensive error handling with structured exceptions
- YAML-based configuration management
- Pipeline visualization capabilities
- Basic test suite with core functionality testing
- Initial benchmark programs for testing
- Basic documentation and user guides

### Educational Focus
- **Configuration Management**: YAML-based configuration with basic validation
- **Error Handling**: Basic exception hierarchy with error reporting
- **Performance Profiling**: Basic execution time profiling
- **Memory Profiling**: Simple memory usage tracking
- **Benchmark Suite**: Initial assembly benchmarks for educational use

### Technical Foundation
- Python 3.8+ support with basic type hints
- Basic code organization and structure
- Simple testing framework
- Initial documentation
- Educational packaging and distribution

### Initial Benchmarks
- Matrix multiplication (basic implementation)
- Bubble sort algorithm (educational version)
- Recursive Fibonacci calculation (simple version)
- Memory access patterns (basic testing)

### Documentation
- Basic user guide
- Installation instructions
- Simple API documentation
- Getting started guide

## [Unreleased]

### Planned Features
- Distributed simulation support
- Real-time performance monitoring
- Machine learning-based performance prediction
- REST API for remote simulation control
- Advanced visualization with interactive charts
- Support for additional instruction set architectures

---

## Support

For questions, bug reports, or feature requests:
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the examples in the `examples/` directory