# Superscalar Pipeline Simulator - Makefile

.PHONY: help install install-dev test lint format type-check clean build docs run-example pre-commit check benchmark docs-serve

# Default target
help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  Superscalar Pipeline Simulator        - Available Commands    ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Installation:"
	@echo "  install          Install the package in production mode"
	@echo "  install-dev      Install with dev dependencies + pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run the full test suite with coverage"
	@echo "  test-fast        Run tests quickly (no coverage, stop on first failure)"
	@echo "  test-coverage    Run tests with detailed coverage report"
	@echo ""
	@echo "Code Quality (Ruff + MyPy):"
	@echo "  lint             Run code linting with ruff (auto-fix)"
	@echo "  lint-check       Run code linting with ruff (check only)"
	@echo "  format           Format code with ruff"
	@echo "  format-check     Check code formatting with ruff"
	@echo "  type-check       Run type checking with mypy"
	@echo "  check            Run all checks (lint + format + type-check + test)"
	@echo "  pre-commit       Run all pre-commit hooks"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  build            Build distribution packages"
	@echo "  clean            Clean build artifacts and cache files"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation (Sphinx HTML)"
	@echo "  docs-clean       Clean documentation build"
	@echo "  docs-serve       Serve documentation locally on port 8000"
	@echo ""
	@echo "Examples:"
	@echo "  run-example      Run basic arithmetic simulation"
	@echo "  run-example-profile  Run simulation with profiling enabled"
	@echo "  run-example-visualize  Run simulation with visualization"
	@echo "  benchmark        Run performance benchmarks"
	@echo ""
	@echo "CI/CD & Release:"
	@echo "  ci-test          Run full CI test suite (lint + type-check + test)"
	@echo "  pre-release      Run all checks and build package"
	@echo "  dev              Quick development cycle (format + lint + test-fast)"
	@echo ""
	@echo "Usage: make <target>"

# Installation
install:
	@echo "Installing package..."
	pip install -e .

install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Development environment ready."

# Testing
test:
	@echo "Running test suite..."
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-fast:
	@echo "Running tests (fast mode)..."
	python -m pytest tests/ -x -v --tb=short

test-coverage:
	@echo "Running tests with detailed coverage..."
	python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/"

# Code Quality (Ruff + MyPy)
lint:
	@echo "Running ruff linter (auto-fix)..."
	python -m ruff check src/ tests/ --fix

lint-check:
	@echo "Checking code with ruff..."
	python -m ruff check src/ tests/

format:
	@echo "Formatting code with ruff..."
	python -m ruff format src/ tests/

format-check:
	@echo "Checking code formatting with ruff..."
	python -m ruff format --check src/ tests/

type-check:
	@echo "Running mypy type checker..."
	python -m mypy src/

# Run all checks
check: lint-check format-check type-check test
	@echo "All critical checks passed."

pre-commit:
	@echo "Running all pre-commit hooks..."
	pre-commit run --all-files

# Clean up
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	rm -f simulation_results.txt
	rm -f benchmark_validation_results.json

# Build
build: clean
	python -m build

# Documentation
docs:
	cd docs && make html

docs-clean:
	cd docs && make clean

docs-serve: docs
	@echo "Serving documentation on http://localhost:8000"
	cd docs/_build/html && python -m http.server 8000

# Examples
run-example:
	@echo "Running basic arithmetic simulation..."
	python main.py --benchmark benchmarks/simple_arithmetic.asm --max-cycles 100

run-example-profile:
	@echo "Running simulation with profiling..."
	python main.py --benchmark benchmarks/simple_sort.asm --profile --max-cycles 200

run-example-visualize:
	@echo "Running simulation with visualization..."
	python main.py --benchmark benchmarks/simple_fibonacci.asm --visualize --max-cycles 200

benchmark:
	@echo "Running performance benchmarks..."
	python -m pytest tests/test_complete_pipeline.py --benchmark

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete."
	@echo "Run 'make test' to verify installation."

# CI/CD targets
ci-test: lint type-check test

# Release preparation
pre-release: clean lint type-check test build
	@echo "Pre-release checks completed successfully."
	@echo "Ready for release."

# Quick development cycle
dev: format lint test-fast
	@echo "Development cycle complete."