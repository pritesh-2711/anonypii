"""
Integration tests using only the regex detector (no model download required).
"""

import pytest

from anonypii import (
    Anonymizer,
    Deanonymizer,
    ReversibleAnonymizer,
)
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.masking.strategies import TagMaskingStrategy, TokenMaskingStrategy
from anonypii.masking.token_generator import HashTokenGenerator
from anonypii.vault.memory import InMemoryVault


@pytest.mark.integration
def test_full_mask_pipeline() -> None:
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        strategy=TagMaskingStrategy(),
    )
    text = "Reach Alice at alice@corp.com or 555-123-4567"
    masked = anon.mask(text)
    assert "alice@corp.com" not in masked
    assert "<EMAIL>" in masked or "[REDACTED]" in masked or "*" in masked


@pytest.mark.integration
def test_full_reversible_pipeline() -> None:
    vault = InMemoryVault()
    ra = ReversibleAnonymizer(
        detector=RegexPIIDetector(),
        vault=vault,
    )
    original = "Contact me at bob@example.com or SSN 123-45-6789"
    result = ra.anonymize(original)
    assert "bob@example.com" not in result.text
    assert "123-45-6789" not in result.text
    restored = ra.restore(result.text)
    assert "bob@example.com" in restored
    assert "123-45-6789" in restored


@pytest.mark.integration
def test_deanonymizer_with_vault() -> None:
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        reversible_strategy=TokenMaskingStrategy(),
    )
    deano = Deanonymizer()
    original = "My email is charlie@test.com"
    result = anon.anonymize(original)
    deano.load_mapping(result.mapping)
    restored = deano.restore_from_vault(result.text)
    assert restored == original


@pytest.mark.integration
def test_hash_generator_idempotent_across_calls() -> None:
    salt = b"stable-salt"
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        reversible_strategy=TokenMaskingStrategy(
            generator=HashTokenGenerator(salt=salt)
        ),
    )
    r1 = anon.anonymize("john@example.com")
    r2 = anon.anonymize("john@example.com")
    assert r1.text == r2.text
    assert r1.mapping == r2.mapping


@pytest.mark.integration
def test_multiple_entity_types_in_one_text() -> None:
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        reversible_strategy=TokenMaskingStrategy(),
    )
    text = "Email: john@example.com, IP: 192.168.1.1, SSN: 123-45-6789"
    result = anon.anonymize(text)
    entity_types = {e.type.value for e in result.entities}
    assert len(entity_types) >= 2
    restored = result.restore()
    assert "john@example.com" in restored


@pytest.mark.integration
def test_audit_log() -> None:
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        audit_log=True,
    )
    anon.mask("john@example.com")
    anon.mask("clean text")
    assert len(anon.audit_records) == 2
    assert anon.audit_records[0]["has_pii"] is True


@pytest.mark.integration
def test_config_path_restricts_entity_types(tmp_path) -> None:
    import yaml

    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.dump({"schema_version": "1.0", "active_entity_types": ["EMAIL"]}),
        encoding="utf-8",
    )
    anon = Anonymizer(
        detector=RegexPIIDetector(),
        config_path=config,
    )
    text = "Email: john@example.com, SSN: 123-45-6789"
    result = anon.anonymize(text)
    types = {e.type.value for e in result.entities}
    assert "EMAIL" in types
    assert "SSN" not in types
