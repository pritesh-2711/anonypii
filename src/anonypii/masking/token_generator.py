"""
Token generators for reversible anonymization placeholders.

Three strategies are provided:

SequentialTokenGenerator
    EMAIL_001, EMAIL_002, PERSON_001, ...
    Counters are per-entity-type, per-instance.  Not deterministic across
    separate instances (use HashTokenGenerator for that).

UUIDTokenGenerator
    EMAIL_a3f2c1b8, PERSON_d91e45c2, ...
    Random short UUIDs.  Non-deterministic.

HashTokenGenerator
    Deterministic: the same input text always produces the same token within
    a session (and across sessions with the same salt).  Safe to use when you
    want idempotent anonymization.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict

from anonypii.core.entities import EntityType


class TokenGenerator(ABC):
    """
    Abstract base for placeholder token generators.

    Subclasses must implement generate(), which returns a string placeholder
    such as ``{{EMAIL_001}}`` that will be substituted into the anonymized text.
    """

    @abstractmethod
    def generate(self, entity_type: EntityType, original_text: str) -> str:
        """
        Produce a placeholder token for the given entity type / text.

        Parameters
        ----------
        entity_type:    The fine-grained entity type.
        original_text:  The raw PII text (used for deduplication by some generators).
        """

    def reset(self) -> None:  # noqa: B027
        """Reset any internal counters.  Default is a no-op."""


class SequentialTokenGenerator(TokenGenerator):
    """
    Produces sequentially numbered tokens per entity type.

    Example:  EMAIL_001, EMAIL_002, PERSON_001
    The counter is per entity-type, per instance.
    Deduplication: the same original_text always gets the same token within
    one instance (stored in _seen cache).
    """

    def __init__(self, prefix: str = "", suffix: str = "", digits: int = 3) -> None:
        self._prefix = prefix
        self._suffix = suffix
        self._digits = digits
        self._counters: dict[str, int] = defaultdict(int)
        self._seen: dict[tuple[str, str], str] = {}

    def generate(self, entity_type: EntityType, original_text: str) -> str:
        key = (entity_type.value, original_text)
        if key in self._seen:
            return self._seen[key]
        self._counters[entity_type.value] += 1
        index = self._counters[entity_type.value]
        token = f"{{{{{self._prefix}{entity_type.value}_{index:0{self._digits}d}{self._suffix}}}}}"
        self._seen[key] = token
        return token

    def reset(self) -> None:
        self._counters.clear()
        self._seen.clear()


class UUIDTokenGenerator(TokenGenerator):
    """
    Produces short UUID-based tokens.

    Example:  {{EMAIL_a3f2c1b8}}, {{PERSON_d91e45c2}}
    Non-deterministic; each call produces a different token even for the same input
    unless the same original text was seen before in this instance.
    """

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], str] = {}

    def generate(self, entity_type: EntityType, original_text: str) -> str:
        key = (entity_type.value, original_text)
        if key in self._seen:
            return self._seen[key]
        short_id = uuid.uuid4().hex[:8]
        token = f"{{{{{entity_type.value}_{short_id}}}}}"
        self._seen[key] = token
        return token

    def reset(self) -> None:
        self._seen.clear()


class HashTokenGenerator(TokenGenerator):
    """
    Produces deterministic tokens by hashing the original text.

    The same original_text + entity_type pair always yields the same token,
    even across separate instances or process restarts, as long as the salt
    is identical.

    This is the recommended generator when idempotent anonymization is required
    (e.g. two documents containing the same email address should produce the
    same placeholder so both can be restored from a single vault entry).

    Parameters
    ----------
    salt:
        Optional bytes added to the hash input to prevent reversal.
        Defaults to a random 16-byte value generated once per instance.
        Pass a fixed value for reproducibility.
    """

    def __init__(self, salt: bytes | None = None) -> None:
        self._salt: bytes = salt if salt is not None else secrets.token_bytes(16)

    def generate(self, entity_type: EntityType, original_text: str) -> str:
        digest = hashlib.blake2b(
            (entity_type.value + ":" + original_text).encode(),
            key=self._salt,
            digest_size=4,
        ).hexdigest()
        return f"{{{{{entity_type.value}_{digest}}}}}"

    def reset(self) -> None:
        pass
