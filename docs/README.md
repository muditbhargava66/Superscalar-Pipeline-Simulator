# Superscalar Pipeline Simulator Documentation

This directory contains comprehensive documentation for the Superscalar Pipeline Simulator.

## Documentation Structure

### User Documentation
- `user_guide.md` - Complete user guide for running simulations
- `installation.md` - Installation instructions for different platforms
- `configuration.md` - Configuration options and parameters
- `benchmarks.md` - Available benchmarks and how to create custom ones

### Developer Documentation
- `architecture.md` - System architecture and design overview
- `api_reference.md` - API documentation for all modules
- `contributing.md` - Guidelines for contributing to the project
- `testing.md` - Testing framework and how to run tests

### Technical Documentation
- `pipeline_design.md` - Detailed pipeline implementation
- `branch_prediction.md` - Branch predictor algorithms
- `cache_system.md` - Cache hierarchy and memory system
- `performance_analysis.md` - Performance metrics and analysis

### Examples and Tutorials
- `examples/` - Example configurations and benchmarks
- `tutorials/` - Step-by-step tutorials
- `case_studies/` - Real-world usage examples

## Building Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -r requirements-dev.txt

# Build HTML documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## Documentation Standards

- Use Markdown for most documentation
- Use reStructuredText for Sphinx-specific features
- Include code examples where appropriate
- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include diagrams and figures when helpful

## Contributing to Documentation

When contributing to the documentation:

1. Follow the existing structure and style
2. Test any code examples
3. Update the table of contents if adding new files
4. Use proper grammar and spelling
5. Include relevant cross-references

For more information, see `contributing.md`.