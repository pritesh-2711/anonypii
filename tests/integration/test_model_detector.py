"""
Integration tests for ModelPIIDetector.

All tests in this file require a downloaded model and are automatically
skipped in CI unless the model is present.

Run locally:
    pytest tests/integration/test_model_detector.py -m requires_model
"""

import pytest

from anonypii.models.downloader import ModelDownloader
from anonypii.models.registry import DEFAULT_MODEL


def _model_available(model_name: str = DEFAULT_MODEL) -> bool:
    return ModelDownloader().is_cached(model_name)


skip_if_no_model = pytest.mark.skipif(
    not _model_available(),
    reason="Model not downloaded. Run: anonypii download piibench-deberta-base",
)


@pytest.mark.requires_model
@skip_if_no_model
def test_model_detector_detect_email() -> None:
    from anonypii.detectors.model import ModelPIIDetector
    from anonypii.core.entities import EntityType

    detector = ModelPIIDetector(model=DEFAULT_MODEL)
    result = detector.detect("My email is alice@example.com")
    emails = [e for e in result.entities if e.type == EntityType.EMAIL]
    assert emails


@pytest.mark.requires_model
@skip_if_no_model
def test_model_detector_batch() -> None:
    from anonypii.detectors.model import ModelPIIDetector

    detector = ModelPIIDetector(model=DEFAULT_MODEL)
    texts = ["alice@example.com", "no pii here", "SSN: 123-45-6789"]
    results = detector.detect_batch(texts)
    assert len(results) == 3
    assert results[0].has_pii
    assert not results[1].has_pii


@pytest.mark.requires_model
@skip_if_no_model
def test_model_anonymizer_roundtrip() -> None:
    from anonypii import ReversibleAnonymizer

    ra = ReversibleAnonymizer(model=DEFAULT_MODEL)
    original = "My email is alice@example.com"
    result = ra.anonymize(original)
    if result.has_pii:
        restored = ra.restore(result.text)
        assert "alice@example.com" in restored


@pytest.mark.requires_model
def test_model_not_downloaded_raises() -> None:
    from anonypii.core.exceptions import ModelNotDownloadedError
    from anonypii.detectors.model import ModelPIIDetector

    with pytest.raises(ModelNotDownloadedError):
        ModelPIIDetector(model=DEFAULT_MODEL, download=False,
                         cache_dir="/tmp/__nonexistent_cache__")
