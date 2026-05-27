"""
Masking strategies for PII anonymization.

Each strategy implements MaskingStrategy and produces a replacement string
for a detected Entity.

Available strategies:

TagMaskingStrategy      <EMAIL>, <PERSON>, <SSN>          — irreversible
RedactedMaskingStrategy [REDACTED]                        — irreversible
StarMaskingStrategy     j***@***.com                      — irreversible, partial
TokenMaskingStrategy    {{EMAIL_001}}                     — reversible
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod

from anonypii.core.entities import Entity
from anonypii.masking.token_generator import SequentialTokenGenerator, TokenGenerator


class MaskingStrategy(ABC):
    """
    Abstract base for all masking strategies.

    Subclasses implement mask(), which receives an Entity and returns the
    replacement string to substitute into the text.
    """

    @abstractmethod
    def mask(self, entity: Entity) -> str:
        """Return the replacement string for the given entity span."""

    @property
    def is_reversible(self) -> bool:
        """True if this strategy produces tokens that can be reversed via a vault."""
        return False


# ---------------------------------------------------------------------------
# Irreversible strategies
# ---------------------------------------------------------------------------


class TagMaskingStrategy(MaskingStrategy):
    """
    Replaces each entity with a typed tag.

    Default:  <EMAIL>, <PERSON>, <SSN>

    Parameters
    ----------
    template:   Format string with ``{entity_type}`` placeholder.
                Default: ``"<{entity_type}>"``
    use_coarse: Use the coarse group name instead of the fine type.
                e.g. <CONTACT> instead of <EMAIL>
    """

    def __init__(
        self,
        template: str = "<{entity_type}>",
        use_coarse: bool = False,
    ) -> None:
        self._template = template
        self._use_coarse = use_coarse

    def mask(self, entity: Entity) -> str:
        label = entity.coarse_group.value if self._use_coarse else entity.type.value
        return self._template.format(entity_type=label)


class RedactedMaskingStrategy(MaskingStrategy):
    """
    Replaces every entity with a fixed placeholder regardless of type.

    Default: ``[REDACTED]``
    """

    def __init__(self, placeholder: str = "[REDACTED]") -> None:
        self._placeholder = placeholder

    def mask(self, entity: Entity) -> str:
        return self._placeholder


class StarMaskingStrategy(MaskingStrategy):
    """
    Partially masks an entity value with asterisks, preserving a configurable
    number of characters at the start and end.

    Examples (keep_start=1, keep_end=1):
        john@example.com  ->  j**************m
        555-123-4567      ->  5**********7
        123-45-6789       ->  1*********9

    When the value is shorter than keep_start + keep_end, the entire value is
    replaced with the min_stars number of asterisks.

    Parameters
    ----------
    keep_start:  Characters to preserve at the beginning (default 1).
    keep_end:    Characters to preserve at the end (default 1).
    min_stars:   Minimum number of asterisks in the middle (default 3).
    star_char:   The masking character (default ``*``).
    preserve_structure:
        When True, the number of stars reflects the actual hidden length.
        When False, always uses min_stars regardless of hidden length.
    """

    def __init__(
        self,
        keep_start: int = 1,
        keep_end: int = 1,
        min_stars: int = 3,
        star_char: str = "*",
        preserve_structure: bool = True,
    ) -> None:
        self._keep_start = keep_start
        self._keep_end = keep_end
        self._min_stars = min_stars
        self._star_char = star_char
        self._preserve_structure = preserve_structure

    def mask(self, entity: Entity) -> str:
        value = entity.text
        total = len(value)
        needed = self._keep_start + self._keep_end

        if total <= needed:
            return self._star_char * self._min_stars

        prefix = value[: self._keep_start]
        suffix = value[total - self._keep_end :]
        hidden_len = total - needed

        if self._preserve_structure:
            stars = self._star_char * max(self._min_stars, hidden_len)
        else:
            stars = self._star_char * self._min_stars

        return f"{prefix}{stars}{suffix}"


# ---------------------------------------------------------------------------
# Reversible strategy
# ---------------------------------------------------------------------------


class TokenMaskingStrategy(MaskingStrategy):
    """
    Replaces each entity with a placeholder token that can be reversed via a vault.

    Default output format:  ``{{EMAIL_001}}``, ``{{PERSON_001}}``

    The token generator handles deduplication: the same original text always
    gets the same token within a session when using SequentialTokenGenerator
    or HashTokenGenerator.

    Parameters
    ----------
    generator:  A TokenGenerator instance.  Defaults to SequentialTokenGenerator.
    """

    def __init__(self, generator: TokenGenerator | None = None) -> None:
        self._generator = generator or SequentialTokenGenerator()

    @property
    def is_reversible(self) -> bool:
        return True

    def mask(self, entity: Entity) -> str:
        return self._generator.generate(entity.type, entity.text)

    def reset(self) -> None:
        """Reset the internal token generator state."""
        self._generator.reset()
