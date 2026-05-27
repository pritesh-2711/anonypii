"""
Anonymizer: the primary public API for PII masking and anonymization.

Two classes are provided:

Anonymizer
    Stateless anonymizer.  mask() returns a plain string; anonymize() returns
    an AnonymizationResult containing the anonymized text and the mapping.

ReversibleAnonymizer
    Stateful convenience wrapper that maintains an internal vault across calls,
    so restore() can be called without explicitly passing the mapping.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Generator, Iterable

from anonypii.config.loader import load_entity_config
from anonypii.core.entities import EntityType
from anonypii.core.exceptions import AnonymizationError
from anonypii.core.result import AnonymizationResult, DetectionResult
from anonypii.detectors.base import OverlapPolicy, PIIDetector
from anonypii.masking.strategies import (
    MaskingStrategy,
    TagMaskingStrategy,
    TokenMaskingStrategy,
)
from anonypii.vault.base import Vault
from anonypii.vault.memory import InMemoryVault


def _require_model_detector(
    model: str,
    download: bool,
    cache_dir: str | Path | None,
    confidence_threshold: float,
    active_entity_types: frozenset[EntityType] | None,
    allowlist: list[str | re.Pattern] | None,
    overlap_policy: OverlapPolicy,
) -> PIIDetector:
    from anonypii.detectors.model import ModelPIIDetector

    return ModelPIIDetector(
        model=model,
        download=download,
        cache_dir=cache_dir,
        confidence_threshold=confidence_threshold,
        active_entity_types=set(active_entity_types) if active_entity_types else None,
        allowlist=allowlist,
        overlap_policy=overlap_policy,
    )


class Anonymizer:
    """
    Stateless PII anonymizer.

    Parameters
    ----------
    detector:
        A PIIDetector instance.  When None, a ModelPIIDetector is constructed
        using ``model`` and ``download`` parameters.
    model:
        Model name to use when no detector is supplied.
        Default: "piibench-deberta-base".
    download:
        Auto-download the model if not cached (only used when detector=None).
    cache_dir:
        Override the model cache directory.
    strategy:
        MaskingStrategy for mask().  Defaults to TagMaskingStrategy (<EMAIL>).
    reversible_strategy:
        MaskingStrategy for anonymize().  Defaults to TokenMaskingStrategy ({{EMAIL_001}}).
    config_path:
        Path to a YAML/JSON entity config file.  None activates all 82 types.
    entity_types:
        Explicit set of entity types to activate.  Takes precedence over config_path.
    confidence_threshold:
        Global minimum confidence threshold passed to the detector.
    confidence_thresholds:
        Per-entity-type confidence overrides.
    allowlist:
        Literal strings or compiled regex patterns to suppress from results.
    overlap_policy:
        How to resolve overlapping entity spans.
    audit_log:
        When True, detection statistics are accumulated in .audit_records.
    """

    def __init__(
        self,
        detector: PIIDetector | None = None,
        model: str = "piibench-deberta-base",
        download: bool = False,
        cache_dir: str | Path | None = None,
        strategy: MaskingStrategy | None = None,
        reversible_strategy: MaskingStrategy | None = None,
        config_path: str | Path | None = None,
        entity_types: set[EntityType] | None = None,
        confidence_threshold: float = 0.5,
        confidence_thresholds: dict[EntityType, float] | None = None,
        allowlist: list[str | re.Pattern] | None = None,
        overlap_policy: OverlapPolicy = OverlapPolicy.LONGEST_SPAN,
        audit_log: bool = False,
    ) -> None:
        active = (
            frozenset(entity_types)
            if entity_types
            else load_entity_config(config_path)
        )

        if detector is not None:
            self._detector = detector
            if active != load_entity_config(None):
                self._detector.active_entity_types = active
        else:
            self._detector = _require_model_detector(
                model=model,
                download=download,
                cache_dir=cache_dir,
                confidence_threshold=confidence_threshold,
                active_entity_types=active,
                allowlist=allowlist,
                overlap_policy=overlap_policy,
            )

        if confidence_thresholds:
            self._detector.confidence_thresholds.update(confidence_thresholds)

        self._mask_strategy: MaskingStrategy = strategy or TagMaskingStrategy()
        self._reversible_strategy: MaskingStrategy = (
            reversible_strategy or TokenMaskingStrategy()
        )
        self._audit_log = audit_log
        self.audit_records: list[dict] = []

    # ------------------------------------------------------------------
    # Public API: irreversible masking
    # ------------------------------------------------------------------

    def mask(self, text: str) -> str:
        """
        Detect PII and replace each entity with its masked form.
        Returns a plain string.  Not reversible.

        Example:
            "My email is john@example.com"  ->  "My email is <EMAIL>"
        """
        result = self._anonymize(text, self._mask_strategy)
        return result.text

    def mask_batch(self, texts: list[str]) -> list[str]:
        """Apply mask() to a list of texts."""
        return [self.mask(t) for t in texts]

    def mask_stream(self, texts: Iterable[str]) -> Generator[str, None, None]:
        """Yield masked strings one at a time from any iterable."""
        for text in texts:
            yield self.mask(text)

    # ------------------------------------------------------------------
    # Public API: reversible anonymization
    # ------------------------------------------------------------------

    def anonymize(self, text: str) -> AnonymizationResult:
        """
        Detect PII and replace each entity with a reversible placeholder token.
        Returns an AnonymizationResult containing the mapping.

        Example:
            "My email is john@example.com"
            -> AnonymizationResult(text="My email is {{EMAIL_001}}", mapping={...})
        """
        return self._anonymize(text, self._reversible_strategy)

    def anonymize_batch(self, texts: list[str]) -> list[AnonymizationResult]:
        """Apply anonymize() to a list of texts."""
        return [self.anonymize(t) for t in texts]

    def anonymize_stream(
        self, texts: Iterable[str]
    ) -> Generator[AnonymizationResult, None, None]:
        """Yield AnonymizationResult objects one at a time from any iterable."""
        for text in texts:
            yield self.anonymize(text)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _anonymize(self, text: str, strategy: MaskingStrategy) -> AnonymizationResult:
        try:
            detection: DetectionResult = self._detector.detect(text)
        except Exception as exc:
            raise AnonymizationError(str(exc)) from exc

        if detection.error:
            return AnonymizationResult(
                text=text,
                original_text=text,
                entities=detection.entities,
                mapping={},
            )

        entities = detection.entities
        mapping: dict[str, str] = {}

        # Apply replacements right-to-left to preserve character offsets
        output = text
        for entity in sorted(entities, key=lambda e: e.start, reverse=True):
            replacement = strategy.mask(entity)
            output = output[: entity.start] + replacement + output[entity.end :]
            if strategy.is_reversible:
                mapping[replacement] = entity.text

        if self._audit_log:
            self.audit_records.append(
                {
                    "entity_count": len(entities),
                    "entity_types": sorted({e.type.value for e in entities}),
                    "has_pii": bool(entities),
                }
            )

        return AnonymizationResult(
            text=output,
            original_text=text,
            entities=entities,
            mapping=mapping,
        )


class ReversibleAnonymizer:
    """
    Stateful anonymizer that maintains an internal vault.

    Calling restore() does not require explicitly passing the mapping —
    the vault accumulates mappings across all anonymize() calls on this instance.

    Parameters
    ----------
    detector:           See Anonymizer.
    model:              See Anonymizer.
    download:           See Anonymizer.
    cache_dir:          See Anonymizer.
    vault:              Vault instance.  Defaults to InMemoryVault().
                        Inject a JsonFileVault for persistent cross-session mappings.
    token_strategy:     MaskingStrategy used for anonymization.
                        Must be a reversible strategy.
                        Defaults to TokenMaskingStrategy with SequentialTokenGenerator.
    config_path:        See Anonymizer.
    entity_types:       See Anonymizer.
    confidence_threshold: See Anonymizer.
    confidence_thresholds: See Anonymizer.
    allowlist:          See Anonymizer.
    overlap_policy:     See Anonymizer.
    audit_log:          See Anonymizer.
    """

    def __init__(
        self,
        detector: PIIDetector | None = None,
        model: str = "piibench-deberta-base",
        download: bool = False,
        cache_dir: str | Path | None = None,
        vault: Vault | None = None,
        token_strategy: MaskingStrategy | None = None,
        config_path: str | Path | None = None,
        entity_types: set[EntityType] | None = None,
        confidence_threshold: float = 0.5,
        confidence_thresholds: dict[EntityType, float] | None = None,
        allowlist: list[str | re.Pattern] | None = None,
        overlap_policy: OverlapPolicy = OverlapPolicy.LONGEST_SPAN,
        audit_log: bool = False,
    ) -> None:
        reversible_strategy = token_strategy or TokenMaskingStrategy()
        if not reversible_strategy.is_reversible:
            raise ValueError(
                "ReversibleAnonymizer requires a reversible MaskingStrategy "
                "(e.g. TokenMaskingStrategy).  "
                f"Got {type(reversible_strategy).__name__}."
            )

        # Store vault first so it is guaranteed to be the injected instance
        self._vault: Vault = vault if vault is not None else InMemoryVault()
        self._anonymizer = Anonymizer(
            detector=detector,
            model=model,
            download=download,
            cache_dir=cache_dir,
            reversible_strategy=reversible_strategy,
            config_path=config_path,
            entity_types=entity_types,
            confidence_threshold=confidence_threshold,
            confidence_thresholds=confidence_thresholds,
            allowlist=allowlist,
            overlap_policy=overlap_policy,
            audit_log=audit_log,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def anonymize(self, text: str) -> AnonymizationResult:
        """
        Anonymize text and store the mapping in the internal vault.
        """
        result = self._anonymizer.anonymize(text)
        self._vault.import_mapping(result.mapping)
        return result

    def restore(self, anonymized_text: str) -> str:
        """
        Restore a previously anonymized text using the internal vault.
        Tokens not in the vault are left as-is.
        """
        return self._vault.restore_text(anonymized_text)

    def restore_from_mapping(self, text: str, mapping: dict[str, str]) -> str:
        """Restore text using an explicit mapping dict."""
        result = text
        for token, original in mapping.items():
            result = result.replace(token, original)
        return result

    @property
    def vault(self) -> Vault:
        """Direct access to the underlying vault."""
        return self._vault

    @property
    def audit_records(self) -> list[dict]:
        return self._anonymizer.audit_records

    def clear_vault(self) -> None:
        """Clear all stored mappings."""
        self._vault.clear()
