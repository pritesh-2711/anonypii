"""
Result types returned by detectors and anonymizers.

Both types are immutable dataclasses with serialization helpers.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from anonypii.core.entities import CoarseGroup, Entity, EntityType


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """
    Output of a detector run against a single text.

    Attributes:
        text:     The original input text (unmodified).
        entities: Detected PII spans, sorted by start offset.
        error:    None on success; error message on per-item failure.
    """

    text: str
    entities: tuple[Entity, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def has_pii(self) -> bool:
        return bool(self.entities)

    @property
    def entity_types(self) -> frozenset[EntityType]:
        return frozenset(e.type for e in self.entities)

    def by_coarse_group(self) -> dict[CoarseGroup, list[Entity]]:
        result: dict[CoarseGroup, list[Entity]] = {}
        for entity in self.entities:
            result.setdefault(entity.coarse_group, []).append(entity)
        return result

    def filter_by_type(self, *types: EntityType) -> DetectionResult:
        kept = tuple(e for e in self.entities if e.type in types)
        return DetectionResult(text=self.text, entities=kept, error=self.error)

    def filter_by_confidence(self, threshold: float) -> DetectionResult:
        kept = tuple(e for e in self.entities if e.confidence >= threshold)
        return DetectionResult(text=self.text, entities=kept, error=self.error)

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "has_pii": self.has_pii,
            "entities": [e.to_dict() for e in self.entities],
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"DetectionResult(has_pii={self.has_pii}, "
            f"entities={len(self.entities)}, error={self.error!r})"
        )


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    """
    Output of an anonymization run.

    For irreversible masking, mapping is empty.
    For reversible anonymization, mapping stores token → original value.

    Attributes:
        text:     The anonymized output text.
        mapping:  Dict of placeholder_token → original_value.
                  Empty for irreversible masking.
        entities: The detected entities that were anonymized.
        original_text: The input text before anonymization.
    """

    text: str
    original_text: str
    entities: tuple[Entity, ...] = field(default_factory=tuple)
    mapping: dict[str, str] = field(default_factory=dict)

    @property
    def has_pii(self) -> bool:
        return bool(self.entities)

    @property
    def is_reversible(self) -> bool:
        return bool(self.mapping)

    @property
    def entity_types(self) -> frozenset[EntityType]:
        return frozenset(e.type for e in self.entities)

    def by_coarse_group(self) -> dict[CoarseGroup, list[Entity]]:
        result: dict[CoarseGroup, list[Entity]] = {}
        for entity in self.entities:
            result.setdefault(entity.coarse_group, []).append(entity)
        return result

    def restore(self) -> str:
        """
        Restore the anonymized text to its original using the stored mapping.
        Only meaningful when is_reversible is True.
        """
        if not self.mapping:
            return self.text
        result = self.text
        for token, original in self.mapping.items():
            result = result.replace(token, original)
        return result

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "original_text": self.original_text,
            "has_pii": self.has_pii,
            "is_reversible": self.is_reversible,
            "entities": [e.to_dict() for e in self.entities],
            "mapping": dict(self.mapping),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str | Path) -> None:
        """Serialize the result to a JSON file."""
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> AnonymizationResult:
        """Deserialize from a JSON file produced by save()."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        entities = tuple(
            Entity(
                text=e["text"],
                type=EntityType(e["type"]),
                start=e["start"],
                end=e["end"],
                confidence=e["confidence"],
            )
            for e in data.get("entities", [])
        )
        return cls(
            text=data["text"],
            original_text=data["original_text"],
            entities=entities,
            mapping=data.get("mapping", {}),
        )

    def __repr__(self) -> str:
        return (
            f"AnonymizationResult(has_pii={self.has_pii}, "
            f"reversible={self.is_reversible}, entities={len(self.entities)})"
        )


def iter_detection_results(
    results: list[DetectionResult],
) -> Iterator[tuple[int, DetectionResult]]:
    """Yield (index, result) pairs — convenience for batch processing."""
    yield from enumerate(results)
