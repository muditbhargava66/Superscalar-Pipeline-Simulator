# Changelog

All notable changes to the Superscalar Pipeline Simulator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06-05

### Critical Gap Fixes
- **Cache Hierarchy Integration**: Execution engine now uses the enhanced `MemoryHierarchy` (L1/L2/main memory) for all memory operations instead of the basic `DataCache`. Cache miss latency is properly tracked as stall cycles.
- **Fixed Statistics Interface**: Corrected method name mismatches (`get_stats()` to `get_statistics()`) for memory hierarchy, execution engine, and register renaming, eliminating fallback to hardcoded values.
- **Dynamic Branch Accuracy**: Replaced hardcoded `branch_accuracy: 90.0` with actual branch predictor statistics computed from prediction/misprediction counters.
- **Cache Hit Rate**: Now computed from actual memory hierarchy statistics instead of hardcoded 95%.

### Execution Engine Bug Fixes
- **Logical Instructions (AND, OR, XOR, NOR, SLL, SRL)**: Fixed `_execute_logical()` in `execution_engine.py` — was writing results to non-existent `instruction.rd` / `instruction.rt` attributes instead of the correct `instruction.destination` field. This caused `'Instruction' object has no attribute 'rd'` errors on every AND/OR/XOR instruction.
- **Shift Instructions (SLL, SRL, SRA)**: Fixed shift amount extraction — was reading non-existent `instruction.immediate` attribute instead of using `_get_immediate_value()` which correctly extracts from `operands[2]`.
- **Comparison Instructions (SLT, SLTI, SLTU, SLTIU)**: Fixed `_execute_comparison()` with the same attribute correction — results are now written to `instruction.destination`.
- **Load Instructions (LW, LH, LB, LBU, LHU)**: Fixed `_execute_load()` to write loaded data to `instruction.destination` instead of the non-existent `instruction.rt`.
- **Operand Extraction**: Updated `_get_rs_value()`, `_get_rt_value()`, and `_get_immediate_value()` to handle `LOGICAL` and `COMPARISON` instruction types in addition to `ARITHMETIC`.
- **Opcode Case-Sensitivity**: Fixed case sensitivity matching across all instruction types (arithmetic, logical, branch, jump) in `execution_engine.py` to prevent failing instruction dispatches.
- **Hazard Tracking for STORE**: Added `rt` (data register) as a tracked source register for `STORE` instructions within the `HazardController`, preventing unhandled structural hazards.
- **Branch and Jump PC Update**: Fixed simulator's main loop to correctly update the Program Counter (PC) upon branch resolution and jump execution, enabling benchmarks with loops to function accurately.
- **Branch Target Extraction**: Corrected single-register branch target extraction (for `bgtz`, `blez`, `bltz`, `bgez`) and `jal` target extraction, eliminating infinite loops caused by jumps to address 0.
- **Benchmark Metric Tracking**: Fixed IPC logging calculations in the simulation loop, allowing benchmarking tables to display true IPC rather than near-zero metrics.

### Branch Predictor Integration
- **Predictor Wired into Simulation Loop**: Branch predictor `predict()` is now called when branch/jump instructions are issued, and `update()` is called with the actual outcome when they complete execution. This replaced the previous 0.0% hardcoded branch accuracy with real prediction results (typically 65–100% depending on workload complexity).
- **ExecutionResult Import**: Added `ExecutionResult` import to `main.py` for branch outcome comparison.

### Branch Predictor Accuracy Fixes
- **TournamentPredictor**: Fixed `update()` to capture predictions BEFORE updating component predictors, eliminating post-update evaluation bias. The meta-predictor's `meta_correct` counter is now properly tracked.
- **Inner BimodalPredictor/GSharePredictor**: Fixed `update()` stat tracking to evaluate correctness using pre-update counter values instead of post-update values.
- **AdaptiveHybridPredictor**: Fixed `update()` to use pre-update predictions for base statistics instead of re-predicting after sub-predictor updates.
- **Accuracy Validation**: Added warmup-based accuracy tests (2000+ branches) verifying Tournament predictor achieves >85% and Bimodal predictor achieves >80% on biased branch patterns.

### New Features
- **Comprehensive Performance Counters**: New `PerformanceCounters` class with detailed pipeline stall breakdown, hazard counters (RAW/WAR/WAW/structural/control), cache counters, branch counters, and ILP tracking.
- **Rename/Commit Bandwidth**: Register renaming now supports configurable `rename_bandwidth` (default 4) and `commit_bandwidth` (default 4) instructions per cycle, matching real superscalar processors.
- **Batch Rename**: New `rename_instruction_batch()` method for high-throughput renaming.
- **Enhanced OOO Execution**: `OutOfOrderExecuteStage` now uses oldest-first priority scheduling and stalls on window overflow instead of dropping instructions.

### GUI and Visualization
- **GUI Parsing Fixes**: Fixed configuration parser throwing exceptions on modern YAML dictionary formats and size strings (e.g., "32KB") to handle files cleanly without failing.
- **Configuration GUI**: Fixed `ConfigurationGUI` class naming, aligned config keys (`cache:` to `memory:`) with main simulator, and added all 6 branch predictor types to the dropdown.
- **GUI Integration**: Added `--gui` CLI flag to `main.py` for launching the configuration GUI directly.
- **GUI Run Simulator**: Rewrote `_run_simulator()` to actually execute the simulation via `subprocess` and display results in a scrollable results window, instead of only showing a "run manually" message box.
- **Visualization Integration**: `PipelineVisualizer` is now wired into the simulation loop -- feeds `PipelineSnapshot` objects every 10 cycles when `--visualize` is enabled. Performance dashboard displays automatically after simulation.

### Benchmarks
- **Extended Benchmark Suite**: Added 4 new benchmarks in subdirectories for advanced workload testing:
  - `integer/dhrystone_like.asm` — Integer-intensive loops, arrays, and string-like ops (~200 instructions)
  - `integer/quicksort.asm` — Quicksort-like partitioning with branch-heavy workload (~150 instructions)
  - `memory/streaming_access.asm` — Sequential, strided, and random-like memory access patterns (~120 instructions)
  - `mixed/compute_intensive.asm` — ALU + memory + branches for realistic IPC measurement (~300 instructions)
- Total benchmark count: **14 benchmarks** (10 root + 4 subdirectory).

### Configuration
- Added `rename_bandwidth`, `commit_bandwidth`, `ooo_execution`, and `ooo_window_size` to `config.yaml`.
- Updated version to 1.2.0 across `pyproject.toml` and `config.yaml`.

### Code Quality & Infrastructure
- **Ruff**: Fixed all linting errors across `src/`, `tests/`, and `main.py` (import sorting, formatting).
- **MyPy**: Resolved all type errors — duplicate module detection (`src.*` → relative imports), dynamic type assignments, unreachable code in `_parse_size`, incorrect `psutil._common.pmem` type annotations.
- **Pre-commit Hooks**: Updated `.pre-commit-config.yaml` to ruff v0.4.10, mypy v1.10.0; added `check-ast`, `debug-statements`, and `check-added-large-files` hooks.
- **pyproject.toml**: Removed invalid `gui` optional dependency, fixed `src/main.py` → `main.py` path, updated dependency versions.
- **Makefile**: Added `run-gui` target, updated `lint`, `format`, and `type-check` targets to include `main.py`.
- **requirements-dev.txt**: Removed unused dependencies (pytest-asyncio, pytest-mock, types-psutil, line-profiler, seaborn, plotly, jupyter, ipykernel); bumped ruff version.
- **Test Suite**: Expanded from 92 to **139 tests** with 100% pass rate.

### Documentation
- **API Reference**: Corrected exception names throughout (`SimulatorError`, `InstructionError`, `PipelineStallError`, `CacheError`, `ExecutionError`, `MemoryAccessError`). Added PerformanceCounters and MemoryHierarchy API sections. Fixed `SimulatorConfig` examples.
- **Design Document**: Updated branch predictor section to list all 6 types. Corrected Future Enhancements section to reflect implemented features.
- **User Guide**: Updated config structure (`memory:` key), added execution config section, fixed CLI options, added all predictor types. Documented all 14 benchmarks organized by category. Added subdirectory benchmark run commands.
- **Installation Guide**: Fixed verification test references and import paths. Added **First-Time User Quick Start** section with 5-step setup guide and troubleshooting table.
- **README.md**: Updated to v1.2.0, 139 tests, 6 branch predictors, 14 benchmarks. Added "Extended Benchmarks (v1.2.0)" table. Fixed Python API example and architecture paths.
- **docs/README.md**: Expanded benchmark table to all 14 entries including `integer/`, `memory/`, `mixed/` subdirectories.

---

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

---

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

---

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
