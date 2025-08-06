# Contributing to Superscalar Pipeline Simulator

Thank you for your interest in contributing to the Superscalar Pipeline Simulator! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of computer architecture and pipeline concepts

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/superscalar-pipeline-simulator.git
   cd superscalar-pipeline-simulator
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```
   
   Or manually:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   pre-commit install
   ```

3. **Verify installation:**
   ```bash
   make test
   ```

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix issues in the existing codebase
- **Feature additions**: Add new functionality
- **Performance improvements**: Optimize existing code
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Examples**: Add new benchmark programs or examples

### Before You Start

1. **Check existing issues**: Look for existing issues or discussions
2. **Create an issue**: For significant changes, create an issue first to discuss
3. **Assign yourself**: Comment on the issue to indicate you're working on it

## Pull Request Process

### 1. Create a Branch

Create a descriptive branch name:
```bash
git checkout -b feature/add-branch-predictor
git checkout -b fix/memory-leak-issue
git checkout -b docs/update-user-guide
```

### 2. Make Changes

- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Test Your Changes

```bash
# Run the full test suite
make test

# Run linting and type checking
make lint
make type-check

# Test specific functionality
python main.py --benchmark benchmarks/benchmark1_matrix_multiplication.asm
```

### 4. Commit Changes

Use clear, descriptive commit messages:
```bash
git add .
git commit -m "feat: add new branch predictor algorithm

- Implement tournament branch predictor
- Add configuration options
- Include comprehensive tests
- Update documentation

Closes #123"
```

### 5. Submit Pull Request

1. Push your branch to your fork
2. Create a pull request with:
   - Clear title and description
   - Reference to related issues
   - Summary of changes
   - Testing performed

## Coding Standards

### Python Style

We use modern Python practices:

- **Python Version**: 3.10+
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all public APIs
- **Formatting**: Ruff for code formatting
- **Linting**: Ruff for code linting
- **Type Checking**: MyPy for static type analysis

### Code Quality Tools

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check
```

### Example Code Style

```python
from typing import Optional, Dict, List
from pathlib import Path

class BranchPredictor:
    """
    Base class for branch predictors.
    
    This class provides the interface that all branch predictors
    must implement for integration with the pipeline simulator.
    
    Args:
        num_entries: Number of prediction table entries
        history_length: Length of branch history to consider
    """
    
    def __init__(self, num_entries: int, history_length: int = 8) -> None:
        self.num_entries = num_entries
        self.history_length = history_length
        self._prediction_table: Dict[int, int] = {}
    
    def predict(self, pc: int, history: Optional[int] = None) -> bool:
        """
        Predict whether a branch will be taken.
        
        Args:
            pc: Program counter of the branch instruction
            history: Branch history for global predictors
            
        Returns:
            True if branch is predicted taken, False otherwise
        """
        # Implementation here
        pass
```

### Configuration

- Use Pydantic models for configuration validation
- Provide sensible defaults
- Document all configuration options
- Support environment variable overrides

### Error Handling

- Use the custom exception hierarchy in `src/exceptions/`
- Provide meaningful error messages with context
- Log errors appropriately
- Handle edge cases gracefully

## Testing

### Test Structure

```
tests/
├── test_branch_prediction.py      # Branch predictor tests
├── test_cache.py                   # Cache system tests
├── test_complete_pipeline.py       # Integration tests
├── test_data_forwarding.py         # Data forwarding tests
├── test_enhanced_features.py       # Enhanced features tests
└── test_pipeline.py                # Pipeline stage tests
```

### Writing Tests

- Use pytest for all tests
- Aim for high test coverage (>80%)
- Include both unit and integration tests
- Test error conditions and edge cases
- Use descriptive test names

Example test:
```python
def test_branch_predictor_accuracy():
    """Test that branch predictor achieves expected accuracy."""
    predictor = GsharePredictor(num_entries=1024, history_length=8)
    
    # Test with known pattern
    correct_predictions = 0
    total_predictions = 100
    
    for i in range(total_predictions):
        prediction = predictor.predict(pc=i * 4)
        actual = (i % 4) < 2  # Known pattern
        predictor.update(pc=i * 4, taken=actual)
        
        if prediction == actual:
            correct_predictions += 1
    
    accuracy = correct_predictions / total_predictions
    assert accuracy > 0.7, f"Expected >70% accuracy, got {accuracy:.1%}"
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_branch_prediction.py -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: User guides and tutorials
3. **API Documentation**: Comprehensive API reference
4. **Architecture Documentation**: Design and implementation details

### Documentation Standards

- Use Markdown for most documentation
- Include code examples where appropriate
- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include diagrams when helpful

### Building Documentation

```bash
# Build HTML documentation
make docs

# Clean and rebuild
make docs-clean docs
```

## Performance Considerations

When contributing performance-sensitive code:

- Profile your changes with the built-in profiler
- Consider memory usage and potential leaks
- Benchmark against existing implementations
- Document performance characteristics

## Submitting Issues

### Bug Reports

Include:
- Python version and operating system
- Complete error message and stack trace
- Minimal code example to reproduce
- Expected vs. actual behavior

### Feature Requests

Include:
- Clear description of the proposed feature
- Use cases and motivation
- Possible implementation approach
- Backward compatibility considerations

## Review Process

All contributions go through code review:

1. **Automated Checks**: CI runs tests, linting, and type checking
2. **Manual Review**: Maintainers review code quality and design
3. **Testing**: Verify functionality works as expected
4. **Documentation**: Ensure documentation is updated

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check the `docs/` directory
- **Examples**: Review code in the `examples/` directory

## Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- Release notes for major features

Thank you for contributing to the Superscalar Pipeline Simulator!