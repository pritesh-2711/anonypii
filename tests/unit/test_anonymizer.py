import re

import pytest

from anonypii.core.anonymizer import Anonymizer, ReversibleAnonymizer
from anonypii.core.entities import Entity, EntityType
from anonypii.core.result import AnonymizationResult
from anonypii.detectors.base import PIIDetector
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.masking.strategies import (
    RedactedMaskingStrategy,
    StarMaskingStrategy,
    TagMaskingStrategy,
    TokenMaskingStrategy,
)
from anonypii.vault.memory import InMemoryVault


def _regex_anonymizer(**kwargs) -> Anonymizer:
    detector = RegexPIIDetector()
    return Anonymizer(detector=detector, **kwargs)


@pytest.mark.unit
class TestAnonymizerMask:
    def test_mask_email_tag_strategy(self) -> None:
        anon = _regex_anonymizer(strategy=TagMaskingStrategy())
        result = anon.mask("My email is john@example.com")
        assert result == "My email is <EMAIL>"

    def test_mask_email_redacted_strategy(self) -> None:
        anon = _regex_anonymizer(strategy=RedactedMaskingStrategy())
        result = anon.mask("My email is john@example.com")
        assert "[REDACTED]" in result

    def test_mask_email_star_strategy(self) -> None:
        anon = _regex_anonymizer(strategy=StarMaskingStrategy(keep_start=1, keep_end=1))
        result = anon.mask("My email is john@example.com")
        assert "j" in result
        assert "*" in result
        assert "john@example.com" not in result

    def test_mask_clean_text_unchanged(self) -> None:
        anon = _regex_anonymizer()
        text = "The sky is blue today."
        assert anon.mask(text) == text

    def test_mask_batch(self) -> None:
        anon = _regex_anonymizer()
        texts = ["john@example.com", "no pii here"]
        results = anon.mask_batch(texts)
        assert len(results) == 2
        assert "john@example.com" not in results[0]
        assert results[1] == "no pii here"

    def test_mask_stream(self) -> None:
        anon = _regex_anonymizer()
        texts = ["john@example.com", "clean"]
        results = list(anon.mask_stream(iter(texts)))
        assert len(results) == 2
        assert "john@example.com" not in results[0]


@pytest.mark.unit
class TestAnonymizerAnonymize:
    def test_anonymize_returns_result(self) -> None:
        anon = _regex_anonymizer(reversible_strategy=TokenMaskingStrategy())
        result = anon.anonymize("My email is john@example.com")
        assert isinstance(result, AnonymizationResult)
        assert result.has_pii
        assert "john@example.com" not in result.text

    def test_anonymize_mapping_populated(self) -> None:
        anon = _regex_anonymizer(reversible_strategy=TokenMaskingStrategy())
        result = anon.anonymize("My email is john@example.com")
        assert result.is_reversible
        assert "john@example.com" in result.mapping.values()

    def test_anonymize_restore_roundtrip(self) -> None:
        anon = _regex_anonymizer(reversible_strategy=TokenMaskingStrategy())
        original = "My email is john@example.com"
        result = anon.anonymize(original)
        assert result.restore() == original

    def test_anonymize_batch(self) -> None:
        anon = _regex_anonymizer(reversible_strategy=TokenMaskingStrategy())
        texts = ["john@example.com", "clean"]
        results = anon.anonymize_batch(texts)
        assert len(results) == 2
        assert results[0].has_pii
        assert not results[1].has_pii

    def test_anonymize_stream(self) -> None:
        anon = _regex_anonymizer(reversible_strategy=TokenMaskingStrategy())
        results = list(anon.anonymize_stream(iter(["john@example.com", "clean"])))
        assert len(results) == 2

    def test_audit_log_accumulates(self) -> None:
        anon = _regex_anonymizer(audit_log=True)
        anon.mask("john@example.com")
        anon.mask("clean text")
        assert len(anon.audit_records) == 2
        assert anon.audit_records[0]["has_pii"] is True
        assert anon.audit_records[1]["has_pii"] is False


@pytest.mark.unit
class TestReversibleAnonymizer:
    def test_anonymize_and_restore(self) -> None:
        ra = ReversibleAnonymizer(
            detector=RegexPIIDetector(),
        )
        original = "My email is john@example.com"
        result = ra.anonymize(original)
        assert ra.restore(result.text) == original

    def test_restore_across_multiple_calls(self) -> None:
        ra = ReversibleAnonymizer(detector=RegexPIIDetector())
        r1 = ra.anonymize("Email: john@example.com")
        r2 = ra.anonymize("SSN: 123-45-6789")
        assert ra.restore(r1.text) == "Email: john@example.com"
        assert ra.restore(r2.text) == "SSN: 123-45-6789"

    def test_restore_from_mapping(self) -> None:
        ra = ReversibleAnonymizer(detector=RegexPIIDetector())
        result = ra.anonymize("john@example.com")
        restored = ra.restore_from_mapping(result.text, result.mapping)
        assert restored == "john@example.com"

    def test_non_reversible_strategy_raises(self) -> None:
        with pytest.raises(ValueError, match="reversible"):
            ReversibleAnonymizer(
                detector=RegexPIIDetector(),
                token_strategy=TagMaskingStrategy(),
            )

    def test_custom_vault_injected(self) -> None:
        vault = InMemoryVault()
        ra = ReversibleAnonymizer(detector=RegexPIIDetector(), vault=vault)
        ra.anonymize("john@example.com")
        # The vault passed in should be the same object and should now hold entries
        assert len(vault) > 0
        assert ra.vault is vault

    def test_clear_vault(self) -> None:
        ra = ReversibleAnonymizer(detector=RegexPIIDetector())
        ra.anonymize("john@example.com")
        ra.clear_vault()
        assert len(ra.vault) == 0
