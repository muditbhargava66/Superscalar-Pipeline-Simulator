# Superscalar Pipeline Simulator - Makefile
# Production-ready build and development commands

.PHONY: help install install-dev test lint format type-check clean build docs run-example

# Default target
help:
	@echo "Superscalar Pipeline Simulator - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install the package in production mode"
	@echo "  install-dev  Install the package in development mode with dev dependencies"
	@echo "  test         Run the test suite"
	@echo "  lint         Run code linting with ruff"
	@echo "  format       Format code with ruff"
	@echo "  type-check   Run type checking with mypy"
	@echo "  clean        Clean build artifacts and cache files"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  build        Build distribution packages"
	@echo "  docs         Build documentation"
	@echo ""
	@echo "Examples:"
	@echo "  run-example  Run example simulation"
	@echo ""
	@echo "Usage: make <target>"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-fast:
	python -m pytest tests/ -x -v

# Code Quality
lint:
	python -m ruff check src/ tests/ --fix

format:
	python -m ruff format src/ tests/

type-check:
	python -m mypy src/

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

# Examples
run-example:
	python main.py --benchmark benchmarks/benchmark1_matrix_multiplication.asm --max-cycles 1000

run-example-profile:
	python main.py --benchmark benchmarks/benchmark3_fibonacci.asm --profile --debug --max-cycles 500

run-example-visualize:
	python main.py --benchmark benchmarks/benchmark2_bubble_sort.asm --visualize --max-cycles 500

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify installation"

# CI/CD targets
ci-test: lint type-check test

# Release preparation
pre-release: clean lint type-check test build
	@echo "Pre-release checks completed successfully!"
	@echo "Ready for GitHub release."

# Quick development cycle
dev: format lint test-fast
	@echo "Development cycle complete!"