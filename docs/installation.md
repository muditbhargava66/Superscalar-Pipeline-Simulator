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
# Test basic import
python -c "import src.main; print('Installation successful!')"

# Run basic tests
python -m pytest tests/test_complete_pipeline.py::TestInstruction -v

# Test GUI (if display available)
python src/gui/config_gui.py

# Run a simple simulation
python src/main.py --config config.yaml --benchmark benchmarks/benchmark1_fixed.asm
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

1. Check the [troubleshooting section](troubleshooting.md)
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

# Setup pre-commit hooks
pre-commit install

# Run tests to verify setup
python -m pytest tests/ -v

# Run linting
python -m ruff check src/

# Run type checking
python -m mypy src/
```

## Next Steps

After successful installation:

1. Read the [User Guide](user_guide.md)
2. Try the [Quick Start Tutorial](tutorials/quickstart.md)
3. Explore the [Example Configurations](examples/)
4. Check out the [API Reference](api_reference.md)

For development:

1. Read the [Contributing Guide](contributing.md)
2. Review the [Architecture Documentation](architecture.md)
3. Check the [Testing Guide](testing.md)