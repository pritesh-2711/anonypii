import threading

import pytest

from anonypii.core.exceptions import VaultWriteError
from anonypii.vault.memory import InMemoryVault, ThreadSafeInMemoryVault


@pytest.mark.unit
class TestInMemoryVault:
    def test_store_and_retrieve(self) -> None:
        vault = InMemoryVault()
        vault.store("{{EMAIL_001}}", "john@example.com")
        assert vault.retrieve("{{EMAIL_001}}") == "john@example.com"

    def test_retrieve_missing_returns_none(self) -> None:
        vault = InMemoryVault()
        assert vault.retrieve("{{MISSING}}") is None

    def test_duplicate_same_value_is_idempotent(self) -> None:
        vault = InMemoryVault()
        vault.store("{{EMAIL_001}}", "john@example.com")
        vault.store("{{EMAIL_001}}", "john@example.com")
        assert len(vault) == 1

    def test_duplicate_different_value_raises(self) -> None:
        vault = InMemoryVault()
        vault.store("{{EMAIL_001}}", "john@example.com")
        with pytest.raises(VaultWriteError):
            vault.store("{{EMAIL_001}}", "other@example.com")

    def test_clear(self) -> None:
        vault = InMemoryVault()
        vault.store("{{T}}", "v")
        vault.clear()
        assert len(vault) == 0

    def test_restore_text(self) -> None:
        vault = InMemoryVault()
        vault.store("{{EMAIL_001}}", "john@example.com")
        restored = vault.restore_text("Contact me at {{EMAIL_001}} please")
        assert restored == "Contact me at john@example.com please"

    def test_restore_text_unknown_token_unchanged(self) -> None:
        vault = InMemoryVault()
        text = "{{UNKNOWN_abc}}"
        assert vault.restore_text(text) == text

    def test_all_mappings(self) -> None:
        vault = InMemoryVault()
        vault.store("{{A}}", "a")
        vault.store("{{B}}", "b")
        m = vault.all_mappings()
        assert m == {"{{A}}": "a", "{{B}}": "b"}

    def test_import_mapping(self) -> None:
        vault = InMemoryVault()
        vault.import_mapping({"{{X}}": "x", "{{Y}}": "y"})
        assert vault.retrieve("{{X}}") == "x"
        assert len(vault) == 2


@pytest.mark.unit
class TestThreadSafeInMemoryVault:
    def test_concurrent_writes(self) -> None:
        vault = ThreadSafeInMemoryVault()
        errors: list[Exception] = []

        def write(i: int) -> None:
            try:
                vault.store(f"{{{{T_{i}}}}}", f"val_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(vault) == 50
