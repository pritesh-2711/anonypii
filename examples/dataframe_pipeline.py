"""
Anonymizing a pandas DataFrame column by column.
Requires: pip install anonypii[pandas]
"""

import pandas as pd

from anonypii import Anonymizer
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.io.dataframe import process_dataframe

data = {
    "name": ["Alice Johnson", "Bob Smith", "Carol White"],
    "email": ["alice@example.com", "bob@corp.com", "carol@hr.org"],
    "notes": [
        "SSN 123-45-6789 on file",
        "Account 5555444433332222",
        "No sensitive data",
    ],
    "department": ["Engineering", "Finance", "HR"],
}
df = pd.DataFrame(data)

anon = Anonymizer(detector=RegexPIIDetector())

# Process all string columns
redacted_df, results_by_col = process_dataframe(df, anon)
print("Redacted DataFrame:")
print(redacted_df.to_string())
print()

# Process only specific columns
redacted_df2, _ = process_dataframe(df, anon, columns=["email", "notes"])
print("Redacted (email + notes only):")
print(redacted_df2.to_string())
print()

# Inspect per-column results
for col, col_results in results_by_col.items():
    pii_rows = [(i, r) for i, r in enumerate(col_results) if r.has_pii]
    print(f"Column '{col}': {len(pii_rows)}/{len(col_results)} rows contain PII")
    for row_idx, r in pii_rows:
        for entity in r.entities:
            print(f"  row {row_idx}: [{entity.type.value}] {entity.text!r}")
