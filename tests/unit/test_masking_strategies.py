import pytest

from anonypii.core.entities import Entity, EntityType
from anonypii.masking.strategies import (
    RedactedMaskingStrategy,
    StarMaskingStrategy,
    TagMaskingStrategy,
    TokenMaskingStrategy,
)
from anonypii.masking.token_generator import (
    HashTokenGenerator,
    SequentialTokenGenerator,
    UUIDTokenGenerator,
)


def _email_entity() -> Entity:
    return Entity(
        text="john@example.com",
        type=EntityType.EMAIL,
        start=0,
        end=16,
        confidence=1.0,
    )


def _ssn_entity() -> Entity:
    return Entity(text="123-45-6789", type=EntityType.SSN, start=0, end=11, confidence=1.0)


@pytest.mark.unit
class TestTagMaskingStrategy:
    def test_default_template(self) -> None:
        s = TagMaskingStrategy()
        assert s.mask(_email_entity()) == "<EMAIL>"

    def test_custom_template(self) -> None:
        s = TagMaskingStrategy(template="[{entity_type}]")
        assert s.mask(_email_entity()) == "[EMAIL]"

    def test_use_coarse(self) -> None:
        s = TagMaskingStrategy(use_coarse=True)
        assert s.mask(_email_entity()) == "<CONTACT>"

    def test_not_reversible(self) -> None:
        assert TagMaskingStrategy().is_reversible is False


@pytest.mark.unit
class TestRedactedMaskingStrategy:
    def test_default(self) -> None:
        s = RedactedMaskingStrategy()
        assert s.mask(_email_entity()) == "[REDACTED]"

    def test_custom_placeholder(self) -> None:
        s = RedactedMaskingStrategy(placeholder="***")
        assert s.mask(_email_entity()) == "***"


@pytest.mark.unit
class TestStarMaskingStrategy:
    def test_basic(self) -> None:
        s = StarMaskingStrategy(keep_start=1, keep_end=1)
        result = s.mask(_email_entity())
        assert result.startswith("j")
        assert result.endswith("m")
        assert "*" in result

    def test_short_value_uses_min_stars(self) -> None:
        short = Entity(text="ab", type=EntityType.EMAIL, start=0, end=2, confidence=1.0)
        s = StarMaskingStrategy(keep_start=1, keep_end=1, min_stars=3)
        assert s.mask(short) == "***"

    def test_preserve_structure_false(self) -> None:
        s = StarMaskingStrategy(keep_start=1, keep_end=1, min_stars=3, preserve_structure=False)
        result = s.mask(_email_entity())
        assert result.count("*") == 3

    def test_custom_star_char(self) -> None:
        s = StarMaskingStrategy(star_char="#")
        result = s.mask(_email_entity())
        assert "#" in result
        assert "*" not in result


@pytest.mark.unit
class TestTokenMaskingStrategy:
    def test_is_reversible(self) -> None:
        assert TokenMaskingStrategy().is_reversible is True

    def test_sequential_format(self) -> None:
        gen = SequentialTokenGenerator()
        s = TokenMaskingStrategy(generator=gen)
        token = s.mask(_email_entity())
        assert token.startswith("{{EMAIL_")
        assert token.endswith("}}")

    def test_same_text_same_token(self) -> None:
        gen = SequentialTokenGenerator()
        s = TokenMaskingStrategy(generator=gen)
        t1 = s.mask(_email_entity())
        t2 = s.mask(_email_entity())
        assert t1 == t2

    def test_different_types_different_counters(self) -> None:
        gen = SequentialTokenGenerator()
        s = TokenMaskingStrategy(generator=gen)
        t_email = s.mask(_email_entity())
        t_ssn = s.mask(_ssn_entity())
        assert "EMAIL" in t_email
        assert "SSN" in t_ssn
        assert t_email != t_ssn

    def test_hash_generator_deterministic(self) -> None:
        salt = b"test-salt-fixed"
        g1 = HashTokenGenerator(salt=salt)
        g2 = HashTokenGenerator(salt=salt)
        s1 = TokenMaskingStrategy(generator=g1)
        s2 = TokenMaskingStrategy(generator=g2)
        assert s1.mask(_email_entity()) == s2.mask(_email_entity())

    def test_uuid_generator_produces_token(self) -> None:
        gen = UUIDTokenGenerator()
        s = TokenMaskingStrategy(generator=gen)
        token = s.mask(_email_entity())
        assert "EMAIL" in token
        assert len(token) > 10
