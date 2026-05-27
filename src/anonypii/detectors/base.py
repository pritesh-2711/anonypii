"""
Base detector abstraction and shared utilities.

All detectors inherit from PIIDetector and implement detect().
The base class provides:

  - Entity filtering by active_entity_types
  - Confidence threshold filtering (global and per-type)
  - Allowlist suppression (literal strings and regex patterns)
  - Overlap resolution (LONGEST_SPAN, HIGHEST_CONFIDENCE, FIRST_WINS)
  - batch_detect() with stream support
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator, Iterable

from anonypii.core.entities import ALL_ENTITY_TYPES, Entity, EntityType
from anonypii.core.result import DetectionResult


class OverlapPolicy(str, Enum):
    """
    Policy for resolving overlapping detected spans.

    LONGEST_SPAN       Keep the longer span; ties go to the first.
    HIGHEST_CONFIDENCE Keep the span with higher confidence; ties to first.
    FIRST_WINS         Keep whichever span starts earliest; ties to longer.
    """

    LONGEST_SPAN = "longest_span"
    HIGHEST_CONFIDENCE = "highest_confidence"
    FIRST_WINS = "first_wins"


class PIIDetector(ABC):
    """
    Abstract base for all PII detectors.

    Parameters
    ----------
    active_entity_types:
        Restrict detection to this set of entity types.
        Defaults to all 82 types.
    confidence_threshold:
        Global minimum confidence for a detection to be included.
        Ignored by rule-based detectors (they always produce 1.0).
    confidence_thresholds:
        Per-entity-type overrides.  Takes precedence over the global threshold.
    allowlist:
        Sequence of literal strings or compiled regex patterns.
        Any detected entity whose text matches at least one allowlist entry
        is suppressed.  Matching is case-sensitive by default.
    overlap_policy:
        How to resolve overlapping detected spans.
        Default: LONGEST_SPAN.
    """

    def __init__(
        self,
        active_entity_types: set[EntityType] | None = None,
        confidence_threshold: float = 0.0,
        confidence_thresholds: dict[EntityType, float] | None = None,
        allowlist: list[str | re.Pattern] | None = None,
        overlap_policy: OverlapPolicy = OverlapPolicy.LONGEST_SPAN,
    ) -> None:
        self.active_entity_types: frozenset[EntityType] = (
            frozenset(active_entity_types) if active_entity_types else ALL_ENTITY_TYPES
        )
        self.confidence_threshold = confidence_threshold
        self.confidence_thresholds: dict[EntityType, float] = confidence_thresholds or {}
        self.overlap_policy = overlap_policy
        self._allowlist: list[str | re.Pattern] = allowlist or []

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _detect_raw(self, text: str) -> list[Entity]:
        """
        Run detection and return raw entities *before* filtering.
        Subclasses implement this; all post-processing happens in detect().
        """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, text: str) -> DetectionResult:
        """
        Run detection on a single text and return a filtered DetectionResult.
        """
        if not text.strip():
            return DetectionResult(text=text, entities=(), error=None)

        try:
            raw = self._detect_raw(text)
        except Exception as exc:
            return DetectionResult(text=text, entities=(), error=str(exc))

        filtered = self._filter(raw)
        resolved = _resolve_overlaps(filtered, self.overlap_policy)
        resolved_sorted = tuple(sorted(resolved, key=lambda e: e.start))
        return DetectionResult(text=text, entities=resolved_sorted)

    def detect_batch(self, texts: list[str]) -> list[DetectionResult]:
        """Run detect() over a list of texts sequentially."""
        return [self.detect(t) for t in texts]

    def detect_stream(
        self, texts: Iterable[str]
    ) -> Generator[DetectionResult, None, None]:
        """Yield DetectionResult objects one at a time from any iterable."""
        for text in texts:
            yield self.detect(text)

    # ------------------------------------------------------------------
    # Allowlist management
    # ------------------------------------------------------------------

    def add_to_allowlist(self, *entries: str | re.Pattern) -> None:
        """Add one or more literal strings or compiled regex patterns."""
        self._allowlist.extend(entries)

    def clear_allowlist(self) -> None:
        self._allowlist.clear()

    # ------------------------------------------------------------------
    # Internal filtering
    # ------------------------------------------------------------------

    def _filter(self, entities: list[Entity]) -> list[Entity]:
        result = []
        for entity in entities:
            if entity.type not in self.active_entity_types:
                continue
            threshold = self.confidence_thresholds.get(
                entity.type, self.confidence_threshold
            )
            if entity.confidence < threshold:
                continue
            if self._is_allowlisted(entity.text):
                continue
            result.append(entity)
        return result

    def _is_allowlisted(self, text: str) -> bool:
        for entry in self._allowlist:
            if isinstance(entry, str):
                if text == entry:
                    return True
            else:
                if entry.search(text):
                    return True
        return False


# ---------------------------------------------------------------------------
# Overlap resolution
# ---------------------------------------------------------------------------


def _resolve_overlaps(entities: list[Entity], policy: OverlapPolicy) -> list[Entity]:
    """
    Remove overlapping entities according to the given policy.

    Two entities overlap when their character spans intersect.
    The policy determines which one to keep.
    """
    if len(entities) <= 1:
        return entities

    # Sort by start offset; ties broken by length (longest first)
    sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
    kept: list[Entity] = []

    for candidate in sorted_entities:
        overlapping = [k for k in kept if _spans_overlap(k, candidate)]
        if not overlapping:
            kept.append(candidate)
            continue

        if policy == OverlapPolicy.FIRST_WINS:
            continue

        if policy == OverlapPolicy.LONGEST_SPAN:
            longest = max(overlapping, key=lambda e: e.end - e.start)
            if (candidate.end - candidate.start) > (longest.end - longest.start):
                for ov in overlapping:
                    kept.remove(ov)
                kept.append(candidate)

        elif policy == OverlapPolicy.HIGHEST_CONFIDENCE:
            max_conf = max(ov.confidence for ov in overlapping)
            if candidate.confidence > max_conf:
                for ov in overlapping:
                    kept.remove(ov)
                kept.append(candidate)

    return kept


def _spans_overlap(a: Entity, b: Entity) -> bool:
    return a.start < b.end and b.start < a.end
