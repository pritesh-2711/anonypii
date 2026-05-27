from pathlib import Path

import pytest

from anonypii.config.loader import load_entity_config
from anonypii.core.entities import ALL_ENTITY_TYPES, EntityType
from anonypii.core.exceptions import EntityTypeNotFoundError, InvalidConfigError


@pytest.mark.unit
def test_none_returns_all_entity_types() -> None:
    result = load_entity_config(None)
    assert result == ALL_ENTITY_TYPES


@pytest.mark.unit
def test_yaml_active_entity_types(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\nactive_entity_types:\n  - EMAIL\n  - SSN\n",
        encoding="utf-8",
    )
    result = load_entity_config(config)
    assert result == frozenset({EntityType.EMAIL, EntityType.SSN})


@pytest.mark.unit
def test_yaml_active_coarse_groups(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\nactive_coarse_groups:\n  - CREDENTIAL\n",
        encoding="utf-8",
    )
    result = load_entity_config(config)
    assert EntityType.SSN in result
    assert EntityType.PASSWORD in result
    assert EntityType.EMAIL not in result


@pytest.mark.unit
def test_yaml_union_of_types_and_groups(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\n"
        "active_entity_types:\n  - EMAIL\n"
        "active_coarse_groups:\n  - CREDENTIAL\n",
        encoding="utf-8",
    )
    result = load_entity_config(config)
    assert EntityType.EMAIL in result
    assert EntityType.SSN in result


@pytest.mark.unit
def test_json_config(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        '{"schema_version": "1.0", "active_entity_types": ["EMAIL", "PHONE"]}',
        encoding="utf-8",
    )
    result = load_entity_config(config)
    assert result == frozenset({EntityType.EMAIL, EntityType.PHONE})


@pytest.mark.unit
def test_unknown_entity_type_raises(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\nactive_entity_types:\n  - NONEXISTENT_TYPE\n",
        encoding="utf-8",
    )
    with pytest.raises(EntityTypeNotFoundError):
        load_entity_config(config)


@pytest.mark.unit
def test_unknown_coarse_group_raises(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\nactive_coarse_groups:\n  - FAKE_GROUP\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidConfigError):
        load_entity_config(config)


@pytest.mark.unit
def test_file_not_found_raises(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfigError, match="file not found"):
        load_entity_config(tmp_path / "nonexistent.yaml")


@pytest.mark.unit
def test_unsupported_schema_version_raises(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("schema_version: '99.0'\n", encoding="utf-8")
    with pytest.raises(InvalidConfigError, match="Unsupported schema_version"):
        load_entity_config(config)


@pytest.mark.unit
def test_empty_lists_return_all_types(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "schema_version: '1.0'\nactive_entity_types: []\nactive_coarse_groups: []\n",
        encoding="utf-8",
    )
    result = load_entity_config(config)
    assert result == ALL_ENTITY_TYPES
