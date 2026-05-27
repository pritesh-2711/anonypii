"""
JSON-file-backed vault with cross-platform file locking.

The vault reads its state from disk on every retrieve() call and writes
atomically (write to temp file, then rename) to survive partial writes.
File locking uses fcntl on POSIX and msvcrt on Windows.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from anonypii.core.exceptions import VaultReadError, VaultWriteError
from anonypii.vault.base import Vault


@contextmanager
def _file_lock(path: Path) -> Generator[None, None, None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_fd = open(lock_path, "w")  # noqa: WPS515
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if sys.platform == "win32":
            import msvcrt

            try:
                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl

            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


class JsonFileVault(Vault):
    """
    Vault that persists token → original mappings to a JSON file.

    Reads from disk on every retrieve() and all_mappings() call.
    Writes are atomic (temp-file + rename).
    Concurrent access is serialised with a cross-platform file lock.

    Parameters
    ----------
    path:
        Path to the JSON file.  Created if it does not exist.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_raw({})

    # ------------------------------------------------------------------
    # Vault interface
    # ------------------------------------------------------------------

    def store(self, token: str, original: str) -> None:
        with _file_lock(self._path):
            data = self._read_raw()
            existing = data.get(token)
            if existing is not None and existing != original:
                raise VaultWriteError(
                    f"Token '{token}' already maps to a different value in vault "
                    f"'{self._path}'. Use a different TokenGenerator or clear."
                )
            if existing == original:
                return
            data[token] = original
            self._write_raw(data)

    def retrieve(self, token: str) -> str | None:
        data = self._read_raw()
        return data.get(token)

    def all_mappings(self) -> dict[str, str]:
        return self._read_raw()

    def clear(self) -> None:
        with _file_lock(self._path):
            self._write_raw({})

    def __len__(self) -> int:
        return len(self._read_raw())

    def __repr__(self) -> str:
        return f"JsonFileVault(path={self._path!r}, entries={len(self)})"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_raw(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            text = self._path.read_text(encoding="utf-8")
            data = json.loads(text) if text.strip() else {}
        except (json.JSONDecodeError, OSError) as exc:
            raise VaultReadError(f"Cannot read vault at '{self._path}': {exc}") from exc
        if not isinstance(data, dict):
            raise VaultReadError(f"Vault file '{self._path}' is corrupt (not a JSON object).")
        return data  # type: ignore[return-value]

    def _write_raw(self, data: dict[str, str]) -> None:
        try:
            dir_ = self._path.parent
            fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".vault_tmp_")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self._path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except OSError as exc:
            raise VaultWriteError(f"Cannot write vault to '{self._path}': {exc}") from exc
