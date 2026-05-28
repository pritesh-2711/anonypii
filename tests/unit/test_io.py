import json
from pathlib import Path

import pytest

from anonypii.core.anonymizer import Anonymizer
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.io.json import process_json_fields, process_json_file
from anonypii.io.text import (
    process_text_file,
    process_text_file_batch,
    write_anonymized_text,
)
from anonypii.masking.strategies import TokenMaskingStrategy


def _anon() -> Anonymizer:
    return Anonymizer(
        detector=RegexPIIDetector(),
        reversible_strategy=TokenMaskingStrategy(),
    )


@pytest.mark.unit
class TestTextIO:
    def test_process_text_file_stream(self, tmp_path: Path) -> None:
        f = tmp_path / "input.txt"
        f.write_text("john@example.com\nno pii here\n", encoding="utf-8")
        anon = _anon()
        results = list(process_text_file(f, anon))
        assert len(results) == 2
        assert results[0].has_pii
        assert not results[1].has_pii

    def test_process_text_file_skip_blank(self, tmp_path: Path) -> None:
        f = tmp_path / "input.txt"
        f.write_text("line one\n\nline two\n", encoding="utf-8")
        anon = _anon()
        results = list(process_text_file(f, anon, skip_blank=True))
        assert len(results) == 2

    def test_process_text_file_batch(self, tmp_path: Path) -> None:
        f = tmp_path / "input.txt"
        f.write_text("john@example.com\nclean\n", encoding="utf-8")
        anon = _anon()
        results = process_text_file_batch(f, anon)
        assert len(results) == 2

    def test_write_anonymized_text(self, tmp_path: Path) -> None:
        f = tmp_path / "input.txt"
        f.write_text("john@example.com\n", encoding="utf-8")
        out = tmp_path / "output.txt"
        anon = _anon()
        results = process_text_file_batch(f, anon)
        write_anonymized_text(results, out)
        content = out.read_text(encoding="utf-8")
        assert "john@example.com" not in content


@pytest.mark.unit
class TestJsonIO:
    def test_process_json_fields_specified(self) -> None:
        data = {"name": "John Doe", "email": "john@example.com", "age": "30"}
        anon = _anon()
        redacted, results = process_json_fields(data, anon, fields=["email"])
        assert "john@example.com" not in redacted["email"]
        assert redacted["name"] == "John Doe"
        assert "email" in results

    def test_process_json_fields_all_strings(self) -> None:
        data = {"email": "john@example.com", "note": "no pii"}
        anon = _anon()
        redacted, results = process_json_fields(data, anon)
        assert len(results) == 2

    def test_process_json_file(self, tmp_path: Path) -> None:
        src = tmp_path / "data.json"
        src.write_text(json.dumps({"email": "john@example.com"}), encoding="utf-8")
        out = tmp_path / "out.json"
        anon = _anon()
        redacted, _ = process_json_file(src, anon, output_path=out)
        assert "john@example.com" not in redacted["email"]
        assert out.exists()
