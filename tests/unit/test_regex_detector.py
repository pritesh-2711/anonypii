import re

import pytest

from anonypii.core.entities import EntityType
from anonypii.detectors.base import OverlapPolicy
from anonypii.detectors.regex import RegexPIIDetector


@pytest.mark.unit
class TestRegexPIIDetector:
    def _detector(self, **kwargs) -> RegexPIIDetector:
        return RegexPIIDetector(**kwargs)

    def test_detects_email(self) -> None:
        d = self._detector()
        r = d.detect("Contact me at john@example.com")
        emails = [e for e in r.entities if e.type == EntityType.EMAIL]
        assert emails
        assert emails[0].text == "john@example.com"

    def test_detects_ssn(self) -> None:
        d = self._detector()
        r = d.detect("SSN: 123-45-6789")
        ssns = [e for e in r.entities if e.type == EntityType.SSN]
        assert ssns
        assert ssns[0].text == "123-45-6789"

    def test_detects_ipv4(self) -> None:
        d = self._detector()
        r = d.detect("Server IP: 192.168.1.1")
        ips = [e for e in r.entities if e.type in (EntityType.IPV4, EntityType.IP_ADDRESS)]
        assert ips

    def test_detects_url(self) -> None:
        d = self._detector()
        r = d.detect("Visit https://example.com for details")
        urls = [e for e in r.entities if e.type == EntityType.URL]
        assert urls

    def test_detects_credit_card(self) -> None:
        d = self._detector()
        r = d.detect("Card: 4111 1111 1111 1111")
        cards = [e for e in r.entities if e.type == EntityType.CREDIT_CARD]
        assert cards

    def test_detects_mac_address(self) -> None:
        d = self._detector()
        r = d.detect("MAC: 00:1A:2B:3C:4D:5E")
        macs = [e for e in r.entities if e.type == EntityType.MAC_ADDRESS]
        assert macs

    def test_clean_text_no_pii(self) -> None:
        d = self._detector()
        r = d.detect("The weather is sunny today.")
        assert not r.has_pii

    def test_confidence_always_1_for_regex(self) -> None:
        d = self._detector()
        r = d.detect("john@example.com")
        for entity in r.entities:
            assert entity.confidence == 1.0

    def test_active_entity_types_filter(self) -> None:
        d = self._detector(active_entity_types={EntityType.EMAIL})
        r = d.detect("Email: john@example.com, SSN: 123-45-6789")
        types = {e.type for e in r.entities}
        assert EntityType.SSN not in types

    def test_allowlist_literal_suppresses_entity(self) -> None:
        d = self._detector(allowlist=["john@example.com"])
        r = d.detect("Email: john@example.com")
        emails = [e for e in r.entities if e.type == EntityType.EMAIL]
        assert not emails

    def test_allowlist_regex_suppresses_entity(self) -> None:
        d = self._detector(allowlist=[re.compile(r".*@example\.com")])
        r = d.detect("Email: john@example.com")
        emails = [e for e in r.entities if e.type == EntityType.EMAIL]
        assert not emails

    def test_allowlist_does_not_suppress_other_entities(self) -> None:
        d = self._detector(allowlist=["john@example.com"])
        r = d.detect("Email: john@example.com, SSN: 123-45-6789")
        ssns = [e for e in r.entities if e.type == EntityType.SSN]
        assert ssns

    def test_add_custom_pattern(self) -> None:
        d = self._detector()
        d.add_pattern(EntityType.UNIQUE_ID, re.compile(r"\bEMP-\d{4}\b"))
        r = d.detect("Employee ID: EMP-1234")
        uid = [e for e in r.entities if e.type == EntityType.UNIQUE_ID]
        assert uid
        assert uid[0].text == "EMP-1234"

    def test_empty_text_returns_no_entities(self) -> None:
        d = self._detector()
        r = d.detect("   ")
        assert not r.has_pii

    def test_detect_batch(self) -> None:
        d = self._detector()
        results = d.detect_batch([
            "john@example.com",
            "no pii here",
            "123-45-6789",
        ])
        assert len(results) == 3
        assert results[0].has_pii
        assert not results[1].has_pii
        assert results[2].has_pii

    def test_detect_stream(self) -> None:
        d = self._detector()
        texts = ["john@example.com", "clean text"]
        results = list(d.detect_stream(iter(texts)))
        assert len(results) == 2
        assert results[0].has_pii

    def test_overlap_policy_first_wins(self) -> None:
        d = self._detector(overlap_policy=OverlapPolicy.FIRST_WINS)
        r = d.detect("john@example.com")
        assert r.entities
