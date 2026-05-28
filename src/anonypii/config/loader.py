"""
Configuration loader for entity type filtering.

Supports YAML and JSON config files.  Falls back to the bundled
entities.yaml (all 82 types active) when no path is supplied.

Config format (YAML example):

    schema_version: "1.0"

    # Fine-grained entity types to activate:
    active_entity_types:
      - EMAIL
      - SSN
      - PERSON

    # Coarse groups to activate (activates ALL types in the group):
    active_coarse_groups:
      - CREDENTIAL
      - FINANCIAL_ID

The resolved active set is the union of both lists.
If both are absent or empty, ALL 82 entity types are active.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from anonypii.core.entities import (
    ALL_ENTITY_TYPES,
    CoarseGroup,
    EntityType,
    entity_types_for_group,
)
from anonypii.core.exceptions import EntityTypeNotFoundError, InvalidConfigError

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
_DEFAULT_CONFIG_PATH = Path(__file__).parent / "entities.yaml"


def load_entity_config(path: str | Path | None = None) -> frozenset[EntityType]:
    """
    Load an entity type config file and return the resolved active set.

    Parameters
    ----------
    path:
        Path to a YAML or JSON config file.  Pass None to activate all 82 types.

    Returns
    -------
    frozenset[EntityType]
        The set of entity types that should be active for detection.
    """
    if path is None:
        return ALL_ENTITY_TYPES

    resolved = Path(path)
    if not resolved.exists():
        raise InvalidConfigError(str(resolved), "file not found")

    try:
        raw = _read_config_file(resolved)
    except Exception as exc:
        raise InvalidConfigError(str(resolved), f"parse error: {exc}") from exc

    _validate_schema_version(raw, str(resolved))

    active: set[EntityType] = set()

    fine_types: list[Any] = raw.get("active_entity_types") or []
    coarse_groups: list[Any] = raw.get("active_coarse_groups") or []

    if not fine_types and not coarse_groups:
        return ALL_ENTITY_TYPES

    for name in fine_types:
        try:
            active.add(EntityType(name))
        except ValueError:
            raise EntityTypeNotFoundError(str(name)) from None

    for name in coarse_groups:
        try:
            group = CoarseGroup(name)
        except ValueError:
            raise InvalidConfigError(
                str(resolved),
                f"Unknown coarse group '{name}'. Valid groups: {[g.value for g in CoarseGroup]}",
            ) from None
        active.update(entity_types_for_group(group))

    return frozenset(active)


def _read_config_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        # Try YAML first, fall back to JSON
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def _validate_schema_version(raw: dict[str, Any], path: str) -> None:
    version = raw.get("schema_version")
    if version is None:
        return
    if str(version) not in SUPPORTED_SCHEMA_VERSIONS:
        raise InvalidConfigError(
            path,
            f"Unsupported schema_version '{version}'. "
            f"Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
        )
