"""
Exception hierarchy for anonypii.

AnonypiiError
├── ModelError
│   ├── ModelNotFoundError        model name not in registry
│   ├── ModelNotDownloadedError   model registered but not in cache
│   ├── ModelLoadError            cached files exist but loading failed
│   └── ModelInferenceError       forward-pass failure
├── ConfigError
│   ├── InvalidConfigError        YAML/JSON parse or schema failure
│   └── EntityTypeNotFoundError   referenced entity type unknown
├── VaultError
│   ├── VaultReadError
│   └── VaultWriteError
├── DetectionError
└── AnonymizationError
"""

from __future__ import annotations


class AnonypiiError(Exception):
    """Base exception for all anonypii errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict = details or {}

    def to_dict(self) -> dict:
        d: dict = {"error": self.__class__.__name__, "message": self.message}
        if self.details:
            d["details"] = self.details
        return d

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


# ---------------------------------------------------------------------------
# Model errors
# ---------------------------------------------------------------------------


class ModelError(AnonypiiError):
    """Base for model-related failures."""


class ModelNotFoundError(ModelError):
    """Requested model name is not in the registry."""

    def __init__(self, model_name: str, available: list[str]) -> None:
        super().__init__(
            f"Model '{model_name}' is not registered. Available: {available}",
            {"model_name": model_name, "available": available},
        )


class ModelNotDownloadedError(ModelError):
    """Model is registered but its weights are not in the local cache."""

    def __init__(self, model_name: str, cache_dir: str) -> None:
        super().__init__(
            f"Model '{model_name}' is not downloaded to '{cache_dir}'.\n"
            f"Download it with:  anonypii download {model_name}\n"
            f"Or at runtime:     ModelPIIDetector(model='{model_name}', download=True)",
            {"model_name": model_name, "cache_dir": cache_dir},
        )


class ModelLoadError(ModelError):
    """Model files are present but could not be loaded."""

    def __init__(self, model_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to load model '{model_name}': {reason}",
            {"model_name": model_name, "reason": reason},
        )


class ModelInferenceError(ModelError):
    """An error occurred during a model forward pass."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"Inference failed: {reason}",
            {"reason": reason},
        )


# ---------------------------------------------------------------------------
# Config errors
# ---------------------------------------------------------------------------


class ConfigError(AnonypiiError):
    """Base for configuration errors."""


class InvalidConfigError(ConfigError):
    """Config file could not be parsed or failed schema validation."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            f"Invalid configuration at '{path}': {reason}",
            {"path": path, "reason": reason},
        )


class EntityTypeNotFoundError(ConfigError):
    """A referenced entity type is not in the known taxonomy."""

    def __init__(self, entity_type: str) -> None:
        super().__init__(
            f"Unknown entity type '{entity_type}'. "
            "Check the bundled entities.yaml for valid names.",
            {"entity_type": entity_type},
        )


# ---------------------------------------------------------------------------
# Vault errors
# ---------------------------------------------------------------------------


class VaultError(AnonypiiError):
    """Base for vault (mapping store) errors."""


class VaultReadError(VaultError):
    """Failed to read from the vault."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Vault read failed: {reason}", {"reason": reason})


class VaultWriteError(VaultError):
    """Failed to write to the vault."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Vault write failed: {reason}", {"reason": reason})


# ---------------------------------------------------------------------------
# Processing errors
# ---------------------------------------------------------------------------


class DetectionError(AnonypiiError):
    """An error occurred during PII detection."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Detection failed: {reason}", {"reason": reason})


class AnonymizationError(AnonypiiError):
    """An error occurred during anonymization."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Anonymization failed: {reason}", {"reason": reason})
