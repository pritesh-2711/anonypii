"""
Regex-based PII detector.

Covers the most common / syntactically structured entity types that can be
reliably detected with patterns.  No model download required.

Supported types (partial coverage — not all 82 entity types are structurally
detectable by regex without false-positive explosion):

  CONTACT:      EMAIL, PHONE, PHONE_NUMBER, FAX_NUMBER
  NETWORK:      IP_ADDRESS, IPV4, IPV6, MAC_ADDRESS, URL
  CREDENTIAL:   SSN, PASSPORT_NUMBER, DRIVER_LICENSE, API_KEY
  FINANCIAL_ID: CREDIT_CARD, IBAN, ACCOUNT_NUMBER, BANK_ROUTING_NUMBER
  TEMPORAL:     DATE, DATE_OF_BIRTH, DATE_TIME
  MISC:         CRYPTO_ADDRESS
"""

from __future__ import annotations

import re

from anonypii.core.entities import Entity, EntityType
from anonypii.detectors.base import OverlapPolicy, PIIDetector

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------
# Each entry: (EntityType, compiled pattern)
# Patterns ordered from most-specific to least-specific within a type group
# to reduce false-positive overlaps.

_PATTERNS: list[tuple[EntityType, re.Pattern[str]]] = [
    # EMAIL
    (
        EntityType.EMAIL,
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            re.IGNORECASE,
        ),
    ),
    # IPV6 (before IPV4 to avoid partial match)
    (
        EntityType.IPV6,
        re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
            r"|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b"
            r"|\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b",
            re.IGNORECASE,
        ),
    ),
    # IPV4
    (
        EntityType.IPV4,
        re.compile(
            r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
            r"(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)){3}\b"
        ),
    ),
    # IP_ADDRESS alias (same pattern as IPV4 for generic detection)
    (
        EntityType.IP_ADDRESS,
        re.compile(
            r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
            r"(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)){3}\b"
        ),
    ),
    # MAC_ADDRESS
    (
        EntityType.MAC_ADDRESS,
        re.compile(
            r"\b(?:[0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b",
            re.IGNORECASE,
        ),
    ),
    # URL (http/https/ftp)
    (
        EntityType.URL,
        re.compile(
            r"\bhttps?://[^\s\"'<>]+|\bftp://[^\s\"'<>]+",
            re.IGNORECASE,
        ),
    ),
    # SSN (US)
    (
        EntityType.SSN,
        re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"),
    ),
    # CREDIT_CARD (Luhn-ish; 13-19 digits with optional separators)
    (
        EntityType.CREDIT_CARD,
        re.compile(r"\b(?:\d[ \-]?){13,19}\b"),
    ),
    # IBAN (basic: 2-letter country + 2 check digits + up to 30 alphanum)
    (
        EntityType.IBAN,
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b"),
    ),
    # BANK_ROUTING_NUMBER (US ABA: 9 digits)
    (
        EntityType.BANK_ROUTING_NUMBER,
        re.compile(r"\b\d{9}\b"),
    ),
    # PHONE / PHONE_NUMBER (common formats)
    (
        EntityType.PHONE,
        re.compile(
            r"(?<!\d)"
            r"(\+?1[\s\-.]?)?"
            r"\(?\d{3}\)?[\s\-.]"
            r"\d{3}[\s\-.]\d{4}"
            r"(?!\d)"
        ),
    ),
    (
        EntityType.PHONE_NUMBER,
        re.compile(r"\b(?:\+\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"),
    ),
    # DATE_OF_BIRTH / DATE (ISO and common formats)
    (
        EntityType.DATE_OF_BIRTH,
        re.compile(
            r"\b(?:DOB|Date\s+of\s+Birth|born\s+on)[:\s]+\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b",
            re.IGNORECASE,
        ),
    ),
    (
        EntityType.DATE,
        re.compile(
            r"\b\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}\b"
            r"|\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"
        ),
    ),
    # PASSPORT_NUMBER (generic 6–9 alphanumeric after keyword)
    (
        EntityType.PASSPORT_NUMBER,
        re.compile(
            r"\b(?:passport(?:\s+number)?|pass\s+no)[:\s.#]*([A-Z0-9]{6,9})\b",
            re.IGNORECASE,
        ),
    ),
    # API_KEY (common patterns: 32+ hex chars, or key-like prefixes)
    (
        EntityType.API_KEY,
        re.compile(
            r"\b(?:api[_\-]?key|access[_\-]?token|bearer|secret)[:\s=]+[A-Za-z0-9_\-\.]{20,}\b",
            re.IGNORECASE,
        ),
    ),
    # CRYPTO_ADDRESS (Bitcoin P2PKH/P2SH, Ethereum)
    (
        EntityType.CRYPTO_ADDRESS,
        re.compile(
            r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"  # Bitcoin P2PKH/P2SH
            r"|0x[a-fA-F0-9]{40}\b",  # Ethereum
        ),
    ),
]


class RegexPIIDetector(PIIDetector):
    """
    Pattern-based PII detector.  No model required; works immediately after
    ``pip install anonypii``.

    Detects structurally identifiable entity types (emails, IPs, phone numbers,
    SSNs, credit cards, IBANs, etc.).  For full 82-type coverage, use
    ModelPIIDetector instead.

    Additional custom patterns can be injected via add_pattern().
    """

    def __init__(
        self,
        active_entity_types: set[EntityType] | None = None,
        confidence_threshold: float = 0.0,
        confidence_thresholds: dict[EntityType, float] | None = None,
        allowlist: list[str | re.Pattern[str]] | None = None,
        overlap_policy: OverlapPolicy = OverlapPolicy.LONGEST_SPAN,
        extra_patterns: list[tuple[EntityType, re.Pattern[str]]] | None = None,
    ) -> None:
        super().__init__(
            active_entity_types=active_entity_types,
            confidence_threshold=confidence_threshold,
            confidence_thresholds=confidence_thresholds,
            allowlist=allowlist,
            overlap_policy=overlap_policy,
        )
        self._patterns: list[tuple[EntityType, re.Pattern[str]]] = list(_PATTERNS)
        if extra_patterns:
            self._patterns.extend(extra_patterns)

    def add_pattern(self, entity_type: EntityType, pattern: re.Pattern[str] | str) -> None:
        """Register an additional regex pattern for a given entity type."""
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._patterns.append((entity_type, pattern))

    def _detect_raw(self, text: str) -> list[Entity]:
        entities: list[Entity] = []
        for entity_type, pattern in self._patterns:
            if entity_type not in self.active_entity_types:
                continue
            for match in pattern.finditer(text):
                span_text = match.group(0).strip()
                if not span_text:
                    continue
                start = match.start() + (len(match.group(0)) - len(match.group(0).lstrip()))
                end = start + len(span_text)
                entities.append(
                    Entity(
                        text=span_text,
                        type=entity_type,
                        start=start,
                        end=end,
                        confidence=1.0,
                    )
                )
        return entities
