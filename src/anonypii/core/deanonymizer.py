"""
Deanonymizer: restore anonymized text to its original form.

Complements Anonymizer for workflows where anonymization and restoration happen
in separate code paths or separate processes.
"""

from __future__ import annotations

from anonypii.vault.base import Vault
from anonypii.vault.memory import InMemoryVault


class Deanonymizer:
    """
    Restores anonymized text using either an explicit mapping dict or a vault.

    Parameters
    ----------
    vault:
        Optional persistent vault.  If provided, restore_from_vault() uses it.
        Defaults to an empty InMemoryVault.
    """

    def __init__(self, vault: Vault | None = None) -> None:
        self._vault: Vault = vault or InMemoryVault()

    def restore(self, text: str, mapping: dict[str, str]) -> str:
        """
        Restore anonymized text using an explicit token → original mapping.

        Tokens not present in the mapping are left unchanged.
        """
        result = text
        for token, original in mapping.items():
            result = result.replace(token, original)
        return result

    def restore_from_vault(self, text: str) -> str:
        """
        Restore anonymized text using the internally held vault.

        Tokens not found in the vault are left unchanged.
        """
        return self._vault.restore_text(text)

    def load_mapping(self, mapping: dict[str, str]) -> None:
        """Import a mapping dict into the internal vault."""
        self._vault.import_mapping(mapping)

    @property
    def vault(self) -> Vault:
        return self._vault
