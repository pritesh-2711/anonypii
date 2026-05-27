import pytest

from anonypii.core.deanonymizer import Deanonymizer
from anonypii.vault.memory import InMemoryVault


@pytest.mark.unit
class TestDeanonymizer:
    def test_restore_from_mapping(self) -> None:
        d = Deanonymizer()
        text = "My email is {{EMAIL_001}}"
        mapping = {"{{EMAIL_001}}": "john@example.com"}
        assert d.restore(text, mapping) == "My email is john@example.com"

    def test_restore_unknown_token_unchanged(self) -> None:
        d = Deanonymizer()
        text = "{{UNKNOWN_abc}}"
        assert d.restore(text, {}) == "{{UNKNOWN_abc}}"

    def test_restore_from_vault(self) -> None:
        vault = InMemoryVault()
        vault.store("{{SSN_001}}", "123-45-6789")
        d = Deanonymizer(vault=vault)
        result = d.restore_from_vault("SSN is {{SSN_001}}")
        assert result == "SSN is 123-45-6789"

    def test_load_mapping_into_vault(self) -> None:
        d = Deanonymizer()
        d.load_mapping({"{{T}}": "val"})
        assert d.vault.retrieve("{{T}}") == "val"

    def test_multiple_tokens_in_one_text(self) -> None:
        d = Deanonymizer()
        mapping = {
            "{{EMAIL_001}}": "john@example.com",
            "{{SSN_001}}": "123-45-6789",
        }
        text = "Email: {{EMAIL_001}}, SSN: {{SSN_001}}"
        result = d.restore(text, mapping)
        assert result == "Email: john@example.com, SSN: 123-45-6789"
