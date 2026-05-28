"""
pandas DataFrame I/O helpers.

Anonymizes specified columns (or all object-dtype columns) in a DataFrame.
"""

from __future__ import annotations

from typing import Any

from anonypii.core.anonymizer import Anonymizer
from anonypii.core.result import AnonymizationResult


def process_dataframe(
    df: Any,
    anonymizer: Anonymizer,
    columns: list[str] | None = None,
    inplace: bool = False,
) -> tuple[Any, dict[str, list[AnonymizationResult]]]:
    """
    Anonymize string columns in a pandas DataFrame.

    Parameters
    ----------
    df:         Input DataFrame.
    anonymizer: Anonymizer instance.
    columns:    Column names to process.  If None, all object-dtype columns are used.
    inplace:    If True, modify df in place.  If False (default), return a copy.

    Returns
    -------
    (result_df, results_by_column)
        result_df: DataFrame with PII replaced in the specified columns
        results_by_column: dict mapping column name → list of AnonymizationResult
                           (one per row)
    """
    try:
        import pandas as pd  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "pandas is required for DataFrame processing. "
            "Install with:  pip install anonypii[pandas]"
        ) from exc

    out = df if inplace else df.copy()
    results_by_column: dict[str, list[AnonymizationResult]] = {}
    target_cols = columns or [c for c in df.columns if df[c].dtype == object]

    for col in target_cols:
        if col not in df.columns:
            continue
        col_results: list[AnonymizationResult] = []
        new_values: list[str] = []
        for value in df[col].fillna("").astype(str):
            result = anonymizer.anonymize(value)
            col_results.append(result)
            new_values.append(result.text)
        out[col] = new_values
        results_by_column[col] = col_results

    return out, results_by_column
