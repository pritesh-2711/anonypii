"""
Extending anonypii with a custom detector and custom regex patterns.
"""

import re

from anonypii import Anonymizer
from anonypii.core.entities import Entity, EntityType
from anonypii.core.result import DetectionResult
from anonypii.detectors.base import PIIDetector
from anonypii.detectors.regex import RegexPIIDetector

# --- Approach 1: Add custom regex pattern to RegexPIIDetector -----------
detector = RegexPIIDetector()
detector.add_pattern(
    EntityType.UNIQUE_ID,
    re.compile(r"\bEMP-\d{4,6}\b"),  # internal employee ID format
)

anon = Anonymizer(detector=detector)
result = anon.anonymize("Employee EMP-12345 has joined the team")
print("Custom pattern result:", result.text)
print("Entities:", [(e.type.value, e.text) for e in result.entities])
print()

# --- Approach 2: Allowlist to suppress known-safe values ----------------
detector2 = RegexPIIDetector(
    allowlist=[
        "noreply@company.com",         # internal no-reply address
        re.compile(r".*@internal\.com$"),  # all internal domain emails
    ]
)

anon2 = Anonymizer(detector=detector2)
texts = [
    "Email noreply@company.com for info",          # suppressed
    "Contact support@internal.com",                # suppressed by pattern
    "Reach alice@external.com for help",           # detected
]
for text in texts:
    result = anon2.mask(text)
    print(f"  {text!r:45s}  ->  {result!r}")

print()

# --- Approach 3: Fully custom detector subclass -------------------------
class KeywordDetector(PIIDetector):
    """Toy detector that flags any word matching a keyword list as MISC."""

    def __init__(self, keywords: list[str]) -> None:
        super().__init__()
        self._keywords = keywords
        self._patterns = [
            (kw, re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE))
            for kw in keywords
        ]

    def _detect_raw(self, text: str) -> list[Entity]:
        entities = []
        for kw, pattern in self._patterns:
            for m in pattern.finditer(text):
                entities.append(
                    Entity(
                        text=m.group(0),
                        type=EntityType.MISC,
                        start=m.start(),
                        end=m.end(),
                        confidence=1.0,
                    )
                )
        return entities


kd = KeywordDetector(["Project-X", "Operation-Y"])
anon3 = Anonymizer(detector=kd)
result3 = anon3.mask("The budget for Project-X was approved today")
print("Custom detector result:", result3)
