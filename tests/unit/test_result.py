import json
from pathlib import Path

import pytest

from anonypii.core.entities import CoarseGroup, Entity, EntityType
from anonypii.core.result import AnonymizationResult, DetectionResult


@pytest.mark.unit
def test_detection_result_has_pii_true(email_entity: Entity) -> None:
    result = DetectionResult(text="my email is test@x.com", entities=(email_entity,))
    assert result.has_pii is True


@pytest.mark.unit
def test_detection_result_has_pii_false() -> None:
    result = DetectionResult(text="hello world", entities=())
    assert result.has_pii is False


@pytest.mark.unit
def test_detection_result_entity_types(email_entity: Entity, ssn_entity: Entity) -> None:
    result = DetectionResult(
        text="...", entities=(email_entity, ssn_entity)
    )
    assert EntityType.EMAIL in result.entity_types
    assert EntityType.SSN in result.entity_types


@pytest.mark.unit
def test_detection_result_by_coarse_group(email_entity: Entity) -> None:
    result = DetectionResult(text="...", entities=(email_entity,))
    groups = result.by_coarse_group()
    assert CoarseGroup.CONTACT in groups
    assert groups[CoarseGroup.CONTACT][0] == email_entity


@pytest.mark.unit
def test_detection_result_filter_by_type(
    email_entity: Entity, ssn_entity: Entity
) -> None:
    result = DetectionResult(text="...", entities=(email_entity, ssn_entity))
    filtered = result.filter_by_type(EntityType.EMAIL)
    assert len(filtered.entities) == 1
    assert filtered.entities[0].type == EntityType.EMAIL


@pytest.mark.unit
def test_detection_result_filter_by_confidence() -> None:
    e1 = Entity(text="a", type=EntityType.EMAIL, start=0, end=1, confidence=0.9)
    e2 = Entity(text="b", type=EntityType.SSN, start=2, end=3, confidence=0.3)
    result = DetectionResult(text="a b", entities=(e1, e2))
    filtered = result.filter_by_confidence(0.5)
    assert len(filtered.entities) == 1
    assert filtered.entities[0].confidence == 0.9


@pytest.mark.unit
def test_detection_result_to_dict(email_entity: Entity) -> None:
    result = DetectionResult(text="test", entities=(email_entity,))
    d = result.to_dict()
    assert d["has_pii"] is True
    assert len(d["entities"]) == 1
    assert d["error"] is None


@pytest.mark.unit
def test_anonymization_result_is_reversible() -> None:
    result = AnonymizationResult(
        text="{{EMAIL_001}}",
        original_text="john@example.com",
        mapping={"{{EMAIL_001}}": "john@example.com"},
    )
    assert result.is_reversible is True
    assert result.restore() == "john@example.com"


@pytest.mark.unit
def test_anonymization_result_restore_empty_mapping() -> None:
    result = AnonymizationResult(
        text="<EMAIL>",
        original_text="john@example.com",
        mapping={},
    )
    assert result.restore() == "<EMAIL>"


@pytest.mark.unit
def test_anonymization_result_save_load(tmp_path: Path) -> None:
    entity = Entity(
        text="john@example.com",
        type=EntityType.EMAIL,
        start=0,
        end=16,
        confidence=0.97,
    )
    result = AnonymizationResult(
        text="{{EMAIL_001}}",
        original_text="john@example.com",
        entities=(entity,),
        mapping={"{{EMAIL_001}}": "john@example.com"},
    )
    out = tmp_path / "result.json"
    result.save(out)
    loaded = AnonymizationResult.load(out)
    assert loaded.text == result.text
    assert loaded.mapping == result.mapping
    assert len(loaded.entities) == 1
