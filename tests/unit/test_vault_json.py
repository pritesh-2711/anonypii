from pathlib import Path

import pytest

from anonypii.core.exceptions import VaultWriteError
from anonypii.vault.json_file import JsonFileVault


@pytest.mark.unit
class TestJsonFileVault:
    def test_store_and_retrieve(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        vault.store("{{EMAIL_001}}", "john@example.com")
        assert vault.retrieve("{{EMAIL_001}}") == "john@example.com"

    def test_persists_across_instances(self, tmp_path: Path) -> None:
        path = tmp_path / "vault.json"
        v1 = JsonFileVault(path)
        v1.store("{{K}}", "value")
        v2 = JsonFileVault(path)
        assert v2.retrieve("{{K}}") == "value"

    def test_duplicate_same_value_idempotent(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        vault.store("{{T}}", "v")
        vault.store("{{T}}", "v")
        assert len(vault) == 1

    def test_duplicate_different_value_raises(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        vault.store("{{T}}", "v1")
        with pytest.raises(VaultWriteError):
            vault.store("{{T}}", "v2")

    def test_clear(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        vault.store("{{T}}", "v")
        vault.clear()
        assert len(vault) == 0

    def test_restore_text(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        vault.store("{{SSN_001}}", "123-45-6789")
        result = vault.restore_text("SSN is {{SSN_001}}")
        assert result == "SSN is 123-45-6789"

    def test_missing_token_left_unchanged(self, tmp_path: Path) -> None:
        vault = JsonFileVault(tmp_path / "vault.json")
        assert vault.restore_text("{{MISSING_x}}") == "{{MISSING_x}}"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "vault.json"
        vault = JsonFileVault(nested)
        vault.store("{{T}}", "v")
        assert nested.exists()
