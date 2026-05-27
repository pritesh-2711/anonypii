"""
anonypii — Production-grade PII detection, masking, and reversible anonymization.

Backed by fine-tuned DeBERTa models from PIIBench (Jha, 2026):
  - piibench-deberta-base  (F1 0.6455, best overall)
  - piibench-deberta-sch   (source-conditioned hierarchical)

Quick start:

    from anonypii import Anonymizer, ReversibleAnonymizer

    # Irreversible masking
    anon = Anonymizer(download=True)
    masked = anon.mask("My email is john@example.com")
    # "My email is <EMAIL>"

    # Reversible anonymization
    result = anon.anonymize("My email is john@example.com")
    # result.text    -> "My email is {{EMAIL_001}}"
    # result.restore() -> "My email is john@example.com"

    # Stateful reversible anonymizer
    ra = ReversibleAnonymizer(download=True)
    r = ra.anonymize("Call me at 555-123-4567")
    original = ra.restore(r.text)
"""

from __future__ import annotations

from anonypii.core.anonymizer import Anonymizer, ReversibleAnonymizer
from anonypii.core.deanonymizer import Deanonymizer
from anonypii.core.entities import (
    ALL_ENTITY_TYPES,
    CoarseGroup,
    Entity,
    EntityType,
    coarse_group_of,
    entity_types_for_group,
)
from anonypii.core.exceptions import (
    AnonypiiError,
    AnonymizationError,
    ConfigError,
    DetectionError,
    EntityTypeNotFoundError,
    InvalidConfigError,
    ModelError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotDownloadedError,
    ModelNotFoundError,
    VaultError,
    VaultReadError,
    VaultWriteError,
)
from anonypii.core.result import AnonymizationResult, DetectionResult
from anonypii.detectors.base import OverlapPolicy, PIIDetector
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.masking.strategies import (
    MaskingStrategy,
    RedactedMaskingStrategy,
    StarMaskingStrategy,
    TagMaskingStrategy,
    TokenMaskingStrategy,
)
from anonypii.masking.token_generator import (
    HashTokenGenerator,
    SequentialTokenGenerator,
    TokenGenerator,
    UUIDTokenGenerator,
)
from anonypii.vault.base import Vault
from anonypii.vault.json_file import JsonFileVault
from anonypii.vault.memory import InMemoryVault, ThreadSafeInMemoryVault

__version__ = "0.1.0"
__author__ = "Pritesh Jha"
__license__ = "Apache-2.0"

__all__ = [
    # Core
    "Anonymizer",
    "ReversibleAnonymizer",
    "Deanonymizer",
    # Entities
    "Entity",
    "EntityType",
    "CoarseGroup",
    "ALL_ENTITY_TYPES",
    "coarse_group_of",
    "entity_types_for_group",
    # Results
    "DetectionResult",
    "AnonymizationResult",
    # Detectors
    "PIIDetector",
    "RegexPIIDetector",
    "OverlapPolicy",
    # Masking
    "MaskingStrategy",
    "TagMaskingStrategy",
    "RedactedMaskingStrategy",
    "StarMaskingStrategy",
    "TokenMaskingStrategy",
    # Token generators
    "TokenGenerator",
    "SequentialTokenGenerator",
    "UUIDTokenGenerator",
    "HashTokenGenerator",
    # Vault
    "Vault",
    "InMemoryVault",
    "ThreadSafeInMemoryVault",
    "JsonFileVault",
    # Exceptions
    "AnonypiiError",
    "ModelError",
    "ModelNotFoundError",
    "ModelNotDownloadedError",
    "ModelLoadError",
    "ModelInferenceError",
    "ConfigError",
    "InvalidConfigError",
    "EntityTypeNotFoundError",
    "VaultError",
    "VaultReadError",
    "VaultWriteError",
    "DetectionError",
    "AnonymizationError",
]
