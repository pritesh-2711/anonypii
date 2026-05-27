.PHONY: help install install-dev lint format typecheck test test-unit test-integration \
        test-all clean build publish download-models

help:
	@echo "anonypii development targets"
	@echo ""
	@echo "Setup:"
	@echo "  make install            Install package (core only)"
	@echo "  make install-dev        Install package + all dev dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  make lint               Run ruff linter"
	@echo "  make format             Run ruff formatter"
	@echo "  make typecheck          Run mypy"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run unit + integration tests (no model)"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-integration   Run integration tests (no model)"
	@echo "  make test-all           Run all tests including model tests"
	@echo "  make test-cov           Run tests with coverage report"
	@echo ""
	@echo "Models:"
	@echo "  make download-models    Download both DeBERTa models"
	@echo ""
	@echo "Release:"
	@echo "  make build              Build wheel and sdist"
	@echo "  make clean              Remove build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/anonypii/ --ignore-missing-imports

test:
	pytest tests/unit/ tests/integration/ -m "not requires_model" -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -m "not requires_model" -v

test-all:
	pytest tests/ -v

test-cov:
	pytest tests/unit/ tests/integration/ -m "not requires_model" \
		--cov=src/anonypii --cov-report=term-missing --cov-report=html

download-models:
	anonypii download all

build:
	pip install build
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	rm -rf htmlcov/ .mypy_cache/ .ruff_cache/
