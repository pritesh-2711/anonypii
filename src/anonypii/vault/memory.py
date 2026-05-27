"""
In-memory vault implementations.

InMemoryVault         — single-threaded, dict-backed, session-scoped
ThreadSafeInMemoryVault — same, with a threading.Lock for concurrent use
"""

from __future__ import annotations

import threading

from anonypii.core.exceptions import VaultWriteError
from anonypii.vault.base import Vault


class InMemoryVault(Vault):
    """
    Dict-backed vault.  Not thread-safe.  Data is lost when the instance is
    garbage-collected.

    Use for single-threaded pipelines or when you do not need persistence.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def store(self, token: str, original: str) -> None:
        existing = self._store.get(token)
        if existing is not None and existing != original:
            raise VaultWriteError(
                f"Token '{token}' already maps to a different value. "
                "Use a different TokenGenerator or clear the vault first."
            )
        self._store[token] = original

    def retrieve(self, token: str) -> str | None:
        return self._store.get(token)

    def all_mappings(self) -> dict[str, str]:
        return dict(self._store)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"InMemoryVault(entries={len(self._store)})"


class ThreadSafeInMemoryVault(Vault):
    """
    Thread-safe variant of InMemoryVault.

    Uses a reentrant lock so the same vault can be safely shared between
    multiple threads (e.g. a thread-pool-based batch processor).
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._lock = threading.RLock()

    def store(self, token: str, original: str) -> None:
        with self._lock:
            existing = self._store.get(token)
            if existing is not None and existing != original:
                raise VaultWriteError(
                    f"Token '{token}' already maps to a different value."
                )
            self._store[token] = original

    def retrieve(self, token: str) -> str | None:
        with self._lock:
            return self._store.get(token)

    def all_mappings(self) -> dict[str, str]:
        with self._lock:
            return dict(self._store)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        with self._lock:
            return f"ThreadSafeInMemoryVault(entries={len(self._store)})"
