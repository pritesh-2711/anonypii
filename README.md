# anonypii

Production-grade PII detection, masking, and reversible anonymization for Python.

Backed by two fine-tuned DeBERTa-v3-base models from the PIIBench research:

| Model | HuggingFace | Full-test F1 | Wins |
|---|---|---:|---|
| `piibench-deberta-base` | [Pritesh-2711/piibench-deberta-base](https://huggingface.co/Pritesh-2711/piibench-deberta-base) | **0.6455** | 54/82 entity types |
| `piibench-deberta-sch` | [Pritesh-2711/piibench-deberta-sch](https://huggingface.co/Pritesh-2711/piibench-deberta-sch) | 0.5894 | 28/82 entity types (HTTP_COOKIE, DATE_TIME, ...) |

Both models cover all **82 entity types** across 10 coarse categories (CREDENTIAL, FINANCIAL_ID, CONTACT, NETWORK, LOCATION, PERSON_GROUP, ORG_ROLE, TEMPORAL, MISC, FINANCIAL_NER).

---

## Installation

```bash
# Core library only (regex detector, no model)
pip install anonypii

# With model support (torch, transformers, huggingface-hub)
pip install anonypii[model]

# With model support + auto-download of both models
pip install anonypii[models]

# With pandas DataFrame support
pip install anonypii[pandas]

# Everything
pip install anonypii[all]
```

### Download models manually

```bash
anonypii download all                    # both models
anonypii download piibench-deberta-base  # recommended only
anonypii download piibench-deberta-sch   # SC+H only
```

Or at runtime:

```python
from anonypii.detectors.model import ModelPIIDetector
detector = ModelPIIDetector(model="piibench-deberta-base", download=True)
```

---

## Quick start

### Irreversible masking

```python
from anonypii import Anonymizer

anon = Anonymizer(model="piibench-deberta-base", download=True)

anon.mask("My email is john@example.com")
# "My email is <EMAIL>"

anon.mask("SSN: 123-45-6789 and card 4111-1111-1111-1111")
# "SSN: <SSN> and card <CREDIT_CARD>"
```

### Reversible anonymization

```python
from anonypii import Anonymizer

anon = Anonymizer(model="piibench-deberta-base", download=True)

result = anon.anonymize("My email is john@example.com")
print(result.text)     # "My email is {{EMAIL_001}}"
print(result.restore()) # "My email is john@example.com"
```

### Stateful reversible anonymizer

```python
from anonypii import ReversibleAnonymizer

ra = ReversibleAnonymizer(model="piibench-deberta-base", download=True)

r = ra.anonymize("Contact alice@corp.com or call 555-123-4567")
print(r.text)           # "Contact {{EMAIL_001}} or call {{PHONE_001}}"
print(ra.restore(r.text)) # original text restored
```

### Using the regex detector (no download needed)

```python
from anonypii import Anonymizer
from anonypii.detectors.regex import RegexPIIDetector

anon = Anonymizer(detector=RegexPIIDetector())
print(anon.mask("john@example.com / 123-45-6789"))
# "<EMAIL> / <SSN>"
```

---

## Masking strategies

```python
from anonypii.masking.strategies import (
    TagMaskingStrategy,        # <EMAIL>          (default for mask())
    RedactedMaskingStrategy,   # [REDACTED]
    StarMaskingStrategy,       # j**************m
    TokenMaskingStrategy,      # {{EMAIL_001}}    (default for anonymize())
)

# Star masking: keep first and last character
from anonypii.masking.strategies import StarMaskingStrategy
anon = Anonymizer(detector=..., strategy=StarMaskingStrategy(keep_start=1, keep_end=1))
```

---

## Entity configuration

Restrict detection to a subset of entities via a YAML or JSON config file:

```yaml
# my_config.yaml
schema_version: "1.0"

active_entity_types:
  - EMAIL
  - SSN
  - CREDIT_CARD

# Or activate entire coarse groups:
active_coarse_groups:
  - CREDENTIAL
  - FINANCIAL_ID
```

```python
anon = Anonymizer(config_path="my_config.yaml", ...)
```

---

## Allowlist

Suppress known-safe values from detection results:

```python
import re
from anonypii.detectors.regex import RegexPIIDetector

detector = RegexPIIDetector(
    allowlist=[
        "noreply@company.com",              # exact literal
        re.compile(r".*@internal\.com$"),   # regex pattern
    ]
)
```

---

## Vault options

```python
from anonypii.vault.memory import InMemoryVault           # default, session-only
from anonypii.vault.memory import ThreadSafeInMemoryVault # thread-safe variant
from anonypii.vault.json_file import JsonFileVault        # persistent across sessions

ra = ReversibleAnonymizer(
    detector=...,
    vault=JsonFileVault("~/.anonypii/vault.json"),
)
```

---

## DataFrame processing

```python
import pandas as pd
from anonypii import Anonymizer
from anonypii.io.dataframe import process_dataframe

df = pd.DataFrame({"email": ["alice@x.com"], "notes": ["SSN 123-45-6789"]})
redacted_df, results = process_dataframe(df, Anonymizer(...))
```

---

## CLI

```bash
anonypii detect  "My email is john@example.com"
anonypii mask    "My email is john@example.com"
anonypii anonymize "My email is john@example.com" --output-mapping mapping.json
anonypii restore   "My email is {{EMAIL_001}}"     --mapping mapping.json
anonypii info
anonypii download all
```

---

## Entity types (82 total)

| Coarse group | Entity types |
|---|---|
| CREDENTIAL | SSN, PASSWORD, API_KEY, PIN, PASSPORT_NUMBER, DRIVER_LICENSE, TAX_ID, NATIONAL_ID, ... |
| FINANCIAL_ID | CREDIT_CARD, IBAN, ACCOUNT_NUMBER, BANK_ROUTING_NUMBER, BIC, SWIFT_BIC, CVV, ... |
| CONTACT | EMAIL, PHONE, PHONE_NUMBER, FAX_NUMBER |
| NETWORK | IP_ADDRESS, IPV4, IPV6, MAC_ADDRESS, URL, USERNAME, HTTP_COOKIE, DEVICE_IDENTIFIER |
| PERSON_GROUP | PERSON, FIRST_NAME, LAST_NAME, NAME, AGE, GENDER |
| LOCATION | ADDRESS, CITY, STATE, COUNTRY, POSTCODE, COORDINATE, STREET_ADDRESS, ... |
| ORG_ROLE | ORG, COMPANY, COMPANY_NAME, JOB, OCCUPATION |
| TEMPORAL | DATE, TIME, DATE_TIME, DATE_OF_BIRTH |
| MISC | CRYPTO_ADDRESS, VEHICLE, CURRENCY, AMOUNT, BLOOD_TYPE, LICENSE_PLATE, ... |
| FINANCIAL_NER | FINANCIAL_ENTITY |

---

## Research

The underlying models are described in:

- **Dataset**: [PIIBench: A Unified Multi-Source Benchmark Corpus for PII Detection](https://arxiv.org/abs/2604.15776) — Jha (2026)
- **Models**: [Fine-Tuning Over Architectural Complexity: PII Detection on PIIBench with DeBERTa](https://arxiv.org/abs/2605.25816) — Jha (2026)

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).
