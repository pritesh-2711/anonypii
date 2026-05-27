"""
JSON document I/O helpers.

Anonymizes specified fields (or all string fields) within a JSON document.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anonypii.core.anonymizer import Anonymizer
from anonypii.core.result import AnonymizationResult


def process_json_fields(
    data: dict[str, Any],
    anonymizer: Anonymizer,
    fields: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, AnonymizationResult]]:
    """
    Anonymize string values in a dict.

    Parameters
    ----------
    data:       Input dict (JSON-like).
    anonymizer: Anonymizer instance.
    fields:     List of top-level field names to process.
                If None, all string-valued fields are processed.

    Returns
    -------
    (redacted_dict, results_by_field)
        redacted_dict: the dict with PII replaced
        results_by_field: AnonymizationResult per processed field
    """
    redacted = dict(data)
    results: dict[str, AnonymizationResult] = {}
    target_fields = fields or [k for k, v in data.items() if isinstance(v, str)]

    for field in target_fields:
        value = data.get(field)
        if not isinstance(value, str):
            continue
        result = anonymizer.anonymize(value)
        redacted[field] = result.text
        results[field] = result

    return redacted, results


def process_json_file(
    path: str | Path,
    anonymizer: Anonymizer,
    fields: list[str] | None = None,
    output_path: str | Path | None = None,
    encoding: str = "utf-8",
) -> tuple[dict[str, Any], dict[str, AnonymizationResult]]:
    """
    Load a JSON file, anonymize the specified fields, and optionally write output.

    Parameters
    ----------
    path:        Input JSON file path.
    anonymizer:  Anonymizer instance.
    fields:      Fields to anonymize (None = all string fields).
    output_path: If provided, write the anonymized JSON here.
    encoding:    File encoding.

    Returns
    -------
    (redacted_dict, results_by_field)
    """
    data = json.loads(Path(path).read_text(encoding=encoding))
    redacted, results = process_json_fields(data, anonymizer, fields)
    if output_path:
        Path(output_path).write_text(
            json.dumps(redacted, indent=2, ensure_ascii=False), encoding=encoding
        )
    return redacted, results
