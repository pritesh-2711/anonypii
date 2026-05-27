# Contributing to anonypii

## Development setup

```bash
git clone https://github.com/pritesh-2711/anonypii
cd anonypii
pip install -e ".[dev]"
pre-commit install
```

## Running tests

```bash
# All tests not requiring a downloaded model (CI-safe)
make test

# Unit tests only
make test-unit

# With coverage
make test-cov

# Full suite including model tests (requires downloaded models)
anonypii download all
make test-all
```

## Code style

The project uses `ruff` for linting and formatting.

```bash
make lint
make format
```

## Type checking

```bash
make typecheck
```

## Pull requests

- Open an issue before large changes.
- Add tests for new behaviour.
- Update CHANGELOG.md under `[Unreleased]`.
- All CI checks must pass.

## Entity taxonomy

The 82 entity types are defined in `src/anonypii/core/entities.py` and mirror
Appendix A of the accompanying PIIBench paper. Adding new entity types requires
updating `EntityType`, `ENTITY_COARSE_MAP`, and `config/entities.yaml`.
