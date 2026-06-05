# Installation Guide

## System Requirements

### Python Version
- Python 3.10 or higher (tested on Python 3.10-3.13)
- pip package manager

### Operating Systems
- macOS 10.15+ (Catalina or later)
- Ubuntu 20.04+ / Debian 11+
- Windows 10+ (with WSL recommended)
- CentOS 8+ / RHEL 8+

### Hardware Requirements
- Minimum: 4GB RAM, 1GB disk space
- Recommended: 8GB RAM, 2GB disk space
- For large simulations: 16GB+ RAM

## Installation Methods

### Method 1: From Source (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git
   cd superscalar-pipeline-simulator
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv

   # On macOS/Linux:
   source venv/bin/activate

   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Basic installation
   pip install -r requirements.txt

   # Development installation (includes testing, linting, docs)
   pip install -r requirements-dev.txt
   ```

4. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git
cd superscalar-pipeline-simulator

# Basic installation
pip install -r requirements.txt

# With development dependencies
pip install -r requirements-dev.txt
```

## Platform-Specific Instructions

### macOS

1. **Install Python 3.10+:**
   ```bash
   # Using Homebrew (recommended)
   brew install python@3.10

   # Or download from python.org
   ```

2. **Install Xcode Command Line Tools (if needed):**
   ```bash
   xcode-select --install
   ```

3. **Follow the general installation steps above**

### Ubuntu/Debian

1. **Update package list:**
   ```bash
   sudo apt update
   ```

2. **Install Python 3.10+ and dependencies:**
   ```bash
   sudo apt install python3.10 python3.10-venv python3.10-dev
   sudo apt install python3-tk  # For GUI support
   sudo apt install build-essential  # For compiling packages
   ```

3. **Follow the general installation steps above**

### Windows

1. **Install Python 3.10+:**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Git:**
   - Download from [git-scm.com](https://git-scm.com/download/win)

3. **Use PowerShell or Command Prompt:**
   ```powershell
   # Follow the general installation steps
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### CentOS/RHEL

1. **Enable EPEL repository:**
   ```bash
   sudo dnf install epel-release  # CentOS 8+
   # or
   sudo yum install epel-release  # CentOS 7
   ```

2. **Install Python 3.10+:**
   ```bash
   sudo dnf install python3.10 python3.10-devel
   sudo dnf install tkinter  # For GUI support
   ```

3. **Follow the general installation steps above**

## Verification

After installation, verify everything works:

```bash
# Run basic simulation
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 50

# Run test suite
python -m pytest tests/ -v

# Test GUI (if display available)
python main.py --gui
# Or directly:
python -c "import sys; sys.path.insert(0, 'src'); from gui.config_gui import main; main()"

# Test examples
python examples/basic_simulation.py
```

### Code Quality Tools Setup

For development, setup the code quality tools:

```bash
# Setup pre-commit hooks (recommended)
pre-commit install

# Manual linting check
ruff check src/ tests/

# Manual formatting check
ruff format --check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Run all pre-commit hooks
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

1. **Python version too old:**
   ```
   Error: Python 3.10+ required
   ```
   **Solution:** Install Python 3.10 or higher

2. **Missing tkinter (GUI issues):**
   ```
   ModuleNotFoundError: No module named '_tkinter'
   ```
   **Solution:**
   - Ubuntu/Debian: `sudo apt install python3-tk`
   - CentOS/RHEL: `sudo dnf install tkinter`
   - macOS: Usually included with Python
   - Windows: Usually included with Python

3. **Import errors:**
   ```
   ImportError: attempted relative import beyond top-level package
   ```
   **Solution:** Make sure you're running from the project root directory

4. **Permission errors on macOS/Linux:**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   **Solution:** Don't use `sudo` with pip in virtual environments

5. **NumPy compilation issues:**
   ```
   Error: Microsoft Visual C++ 14.0 is required
   ```
   **Solution:** Install Visual Studio Build Tools on Windows

### Getting Help

If you encounter issues:

1. Check common issues below
2. Search existing [GitHub issues](https://github.com/muditbhargava66/superscalar-pipeline-simulator/issues)
3. Create a new issue with:
   - Your operating system and Python version
   - Complete error message
   - Steps to reproduce the problem

## Development Setup

For developers contributing to the project:

```bash
# Clone and setup
git clone https://github.com/muditbhargava66/superscalar-pipeline-simulator.git
cd superscalar-pipeline-simulator

# Create development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Setup pre-commit hooks (runs linting/formatting before each commit)
pre-commit install

# Run tests to verify setup
python -m pytest tests/ -v

# Run linting
ruff check src/ tests/

# Run formatting
ruff format src/ tests/

# Run type checking
mypy src/ --ignore-missing-imports
```

## Next Steps

After successful installation:

1. Read the [User Guide](user_guide.md)
2. Try the [Example Scripts](../examples/)
3. Explore the [Configuration Reference](../config.yaml)
4. Check out the [API Reference](api_reference.md)

For development:

1. Read the [Contributing Guide](../CONTRIBUTING.md)
2. Review the [Design Document](design_document.md)
3. Run the test suite: `python -m pytest tests/ -v`

---

## First-Time User Quick Start

If you've just cloned the repository and want to get running immediately:

### Step 1: Set up your environment

```bash
# Navigate to the project directory
cd Superscalar-Pipeline-Simulator-

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Optional: for development
```

### Step 2: Verify installation

```bash
# Run the test suite (should show 139 passing tests)
python -m pytest tests/ -v

# Run a simple simulation
python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100
```

### Step 3: Try different benchmarks

```bash
# Simple sorting
python main.py --benchmark benchmarks/simple_sort.asm --max-cycles 100

# Fibonacci with profiling
python main.py --benchmark benchmarks/simple_fibonacci.asm --max-cycles 100 --profile

# Advanced: integer workload benchmark
python main.py --benchmark benchmarks/integer/dhrystone_like.asm --max-cycles 200 --profile

# Advanced: mixed compute-intensive benchmark
python main.py --benchmark benchmarks/mixed/compute_intensive.asm --max-cycles 300 --profile
```

### Step 4: Launch the GUI (optional)

```bash
# Launch the configuration GUI (requires tkinter)
python main.py --gui

# Or with a benchmark pre-loaded
python main.py --gui --benchmark benchmarks/simple_arithmetic.asm
```

### Step 5: Explore further

- See all available benchmarks in `benchmarks/` (including `integer/`, `memory/`, `mixed/` subdirectories)
- Try different branch predictors: edit `config.yaml` and change `branch_predictor.type`
- Enable visualization: add `--visualize` flag
- Read the [User Guide](user_guide.md) for detailed documentation

### Troubleshooting First Run

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Make sure you're in the project root and have run `pip install -r requirements.txt` |
| `No module named '_tkinter'` | Install tkinter: macOS usually includes it; Linux: `sudo apt install python3-tk` |
| `Execution error for AND` | This was fixed in v1.2.0 — pull the latest code |
| GUI exits silently | Ensure you have a display available; try running without `--gui` first |
| Tests fail | Run `pip install -r requirements-dev.txt` then `python -m pytest tests/ -v` |
