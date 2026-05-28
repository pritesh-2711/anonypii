"""
Plain text file I/O helpers.

process_text_file()      — anonymize a .txt file line by line
process_text_file_batch()— load all lines then process in one batch call
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from anonypii.core.anonymizer import Anonymizer
from anonypii.core.result import AnonymizationResult


def process_text_file(
    path: str | Path,
    anonymizer: Anonymizer,
    *,
    skip_blank: bool = True,
    encoding: str = "utf-8",
) -> Generator[AnonymizationResult, None, None]:
    """
    Yield an AnonymizationResult for each line in a text file.

    Streams line by line; suitable for large files.

    Parameters
    ----------
    path:         Path to the input .txt file.
    anonymizer:   Anonymizer instance to use.
    skip_blank:   Skip blank lines (default True).
    encoding:     File encoding (default utf-8).
    """
    with Path(path).open(encoding=encoding) as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            if skip_blank and not stripped.strip():
                continue
            yield anonymizer.anonymize(stripped)


def process_text_file_batch(
    path: str | Path,
    anonymizer: Anonymizer,
    *,
    skip_blank: bool = True,
    encoding: str = "utf-8",
) -> list[AnonymizationResult]:
    """
    Load all lines from a text file and anonymize them in one batch call.

    Loads the full file into memory; use process_text_file() for large files.
    """
    with Path(path).open(encoding=encoding) as fh:
        lines = [line.rstrip("\n") for line in fh if not skip_blank or line.strip()]
    return anonymizer.anonymize_batch(lines)


def write_anonymized_text(
    results: list[AnonymizationResult],
    path: str | Path,
    encoding: str = "utf-8",
) -> None:
    """Write the anonymized text of each result as a line in a file."""
    with Path(path).open("w", encoding=encoding) as f:
        for result in results:
            f.write(result.text + "\n")
