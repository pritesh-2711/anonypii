"""
pytest configuration and shared fixtures.
"""

from __future__ import annotations

import pytest

from anonypii.core.entities import Entity, EntityType
from anonypii.detectors.base import PIIDetector

# ---------------------------------------------------------------------------
# Custom pytest markers
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_model: test requires a downloaded model (skip with -m 'not requires_model')",
    )
    config.addinivalue_line("markers", "integration: integration test")
    config.addinivalue_line("markers", "unit: unit test")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def email_entity() -> Entity:
    return Entity(
        text="john@example.com",
        type=EntityType.EMAIL,
        start=12,
        end=28,
        confidence=0.97,
    )


@pytest.fixture
def ssn_entity() -> Entity:
    return Entity(
        text="123-45-6789",
        type=EntityType.SSN,
        start=39,
        end=50,
        confidence=0.95,
    )


@pytest.fixture
def sample_text_with_pii() -> str:
    return "My email is john@example.com and SSN is 123-45-6789"


@pytest.fixture
def sample_text_clean() -> str:
    return "The quarterly revenue increased by 12 percent."


class _StubDetector(PIIDetector):
    """A detector that returns a fixed list of entities for testing."""

    def __init__(self, entities: list[Entity]) -> None:
        super().__init__()
        self._entities = entities

    def _detect_raw(self, text: str) -> list[Entity]:
        return self._entities


@pytest.fixture
def stub_detector_factory():
    """Returns a factory that creates a StubDetector with given entities."""
    return _StubDetector
