"""
Vault abstraction for storing token → original PII mappings.

A vault is a simple key-value store where:
    key   = placeholder token  (e.g. "{{EMAIL_001}}")
    value = original PII text  (e.g. "john@example.com")

Vault implementations must be injected into the Anonymizer; no global state is used.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

# Token pattern: {{SOME_TYPE_id}} — matches generated placeholder tokens
_TOKEN_PATTERN: re.Pattern[str] = re.compile(r"\{\{[A-Z_]+_[A-Za-z0-9]+\}\}")


class Vault(ABC):
    """
    Abstract base for PII mapping stores.

    All vault operations should be idempotent on duplicate keys:
    storing the same token with the same value twice is a no-op.
    Storing the same token with a *different* value raises VaultWriteError.
    """

    @abstractmethod
    def store(self, token: str, original: str) -> None:
        """Persist a token → original mapping."""

    @abstractmethod
    def retrieve(self, token: str) -> str | None:
        """
        Return the original value for the given token, or None if unknown.
        Implementations should NOT raise on missing keys.
        """

    @abstractmethod
    def all_mappings(self) -> dict[str, str]:
        """Return a copy of all stored mappings."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored mappings."""

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of stored mappings."""

    def restore_text(self, text: str) -> str:
        """
        Replace all placeholder tokens in ``text`` with their originals.

        Tokens that are not in the vault are left as-is.
        """

        def _replace(match: re.Match[str]) -> str:
            token = match.group(0)
            original = self.retrieve(token)
            if original is None:
                return token
            return original

        return _TOKEN_PATTERN.sub(_replace, text)

    def import_mapping(self, mapping: dict[str, str]) -> None:
        """Bulk-import a token → original mapping dict into the vault."""
        for token, original in mapping.items():
            self.store(token, original)
