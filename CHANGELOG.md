# Changelog

All notable changes to anonypii will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.1.0] — 2026-05-27

### Added

- Initial release.
- `Anonymizer` with irreversible masking (`mask()`) and reversible anonymization (`anonymize()`).
- `ReversibleAnonymizer` stateful wrapper maintaining an internal vault across calls.
- `Deanonymizer` for explicit token-to-original restoration.
- `RegexPIIDetector` — pattern-based detector, no model required.
- `ModelPIIDetector` — DeBERTa-based detector supporting two models:
  - `piibench-deberta-base` (F1 0.6455, recommended)
  - `piibench-deberta-sch` (source-conditioned hierarchical, stronger on 28 entity types)
- Full 82-entity taxonomy from PIIBench (Jha, 2026), grouped into 10 coarse categories.
- Four masking strategies: `TagMaskingStrategy`, `RedactedMaskingStrategy`, `StarMaskingStrategy`, `TokenMaskingStrategy`.
- Three token generators: `SequentialTokenGenerator`, `UUIDTokenGenerator`, `HashTokenGenerator`.
- Two vault implementations: `InMemoryVault`, `ThreadSafeInMemoryVault`, `JsonFileVault`.
- YAML/JSON entity config with `schema_version` validation.
- Coarse group filtering in config (`active_coarse_groups`).
- Allowlist supporting literal strings and compiled regex patterns.
- Per-entity-type confidence thresholds.
- Overlap resolution policies: `LONGEST_SPAN`, `HIGHEST_CONFIDENCE`, `FIRST_WINS`.
- Audit log mode (`audit_log=True`).
- Streaming processing (`mask_stream()`, `anonymize_stream()`, `detect_stream()`).
- `AnonymizationResult.save()` / `AnonymizationResult.load()` for JSON serialization.
- `io.text`, `io.json`, `io.dataframe` processing helpers.
- CLI: `detect`, `mask`, `anonymize`, `restore`, `download`, `info`.
- Model download management with `ModelDownloader` and `anonypii download` CLI.
- Post-install hook for `pip install anonypii[models]`.
- GitHub Actions: CI, release to PyPI, CodeQL.
- Full unit and integration test suite (pytest, no model required for CI).
