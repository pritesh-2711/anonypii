import pytest

from anonypii.core.entities import (
    ALL_ENTITY_TYPES,
    CoarseGroup,
    Entity,
    EntityType,
    coarse_group_of,
    entity_types_for_group,
)


@pytest.mark.unit
def test_all_entity_types_count() -> None:
    assert len(ALL_ENTITY_TYPES) == 82


@pytest.mark.unit
def test_every_entity_type_has_coarse_group() -> None:
    for et in EntityType:
        group = coarse_group_of(et)
        assert isinstance(group, CoarseGroup)


@pytest.mark.unit
def test_entity_types_for_group_financial_id() -> None:
    types = entity_types_for_group(CoarseGroup.FINANCIAL_ID)
    assert EntityType.IBAN in types
    assert EntityType.CREDIT_CARD in types
    assert EntityType.EMAIL not in types


@pytest.mark.unit
def test_entity_coarse_property() -> None:
    entity = Entity(
        text="john@example.com",
        type=EntityType.EMAIL,
        start=0,
        end=16,
        confidence=1.0,
    )
    assert entity.coarse_group == CoarseGroup.CONTACT


@pytest.mark.unit
def test_entity_to_dict() -> None:
    entity = Entity(
        text="123-45-6789",
        type=EntityType.SSN,
        start=0,
        end=11,
        confidence=0.95,
    )
    d = entity.to_dict()
    assert d["text"] == "123-45-6789"
    assert d["type"] == "SSN"
    assert d["coarse_group"] == "CREDENTIAL"
    assert d["confidence"] == 0.95


@pytest.mark.unit
def test_entity_is_frozen() -> None:
    entity = Entity(text="x", type=EntityType.EMAIL, start=0, end=1, confidence=1.0)
    with pytest.raises(AttributeError):
        entity.text = "y"  # type: ignore[misc]


@pytest.mark.unit
def test_coarse_groups_cover_all_types() -> None:
    from anonypii.core.entities import ENTITY_COARSE_MAP

    for et in EntityType:
        assert et in ENTITY_COARSE_MAP, f"{et} missing from ENTITY_COARSE_MAP"
