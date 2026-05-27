"""
Restricting detection to a subset of entity types via config file.
"""

import tempfile
from pathlib import Path

import yaml

from anonypii import Anonymizer
from anonypii.detectors.regex import RegexPIIDetector

# --- Config file: activate only CONTACT types ---------------------------
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".yaml", delete=False, encoding="utf-8"
) as f:
    yaml.dump(
        {
            "schema_version": "1.0",
            "active_coarse_groups": ["CONTACT"],
        },
        f,
    )
    config_path = f.name

anon = Anonymizer(
    detector=RegexPIIDetector(),
    config_path=config_path,
)
text = "Email: john@example.com, SSN: 123-45-6789, IP: 192.168.1.1"
result = anon.anonymize(text)
print("Input  :", text)
print("Output :", result.text)
print("Types  :", [e.type.value for e in result.entities])
# Only EMAIL/PHONE types; SSN and IP_ADDRESS are suppressed

# --- Config via explicit entity_types set --------------------------------
anon2 = Anonymizer(
    detector=RegexPIIDetector(),
    entity_types={"EMAIL", "SSN"},  # type: ignore[arg-type]
)
# equivalently:
from anonypii.core.entities import EntityType

anon3 = Anonymizer(
    detector=RegexPIIDetector(),
    entity_types={EntityType.EMAIL, EntityType.SSN},
)
result3 = anon3.anonymize(text)
print("\nWith EMAIL+SSN only:")
print("Output:", result3.text)
print("Types :", [e.type.value for e in result3.entities])

Path(config_path).unlink(missing_ok=True)
