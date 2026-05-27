"""
Basic masking examples using the regex detector (no model download required).
"""

from anonypii import Anonymizer
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.masking.strategies import (
    RedactedMaskingStrategy,
    StarMaskingStrategy,
    TagMaskingStrategy,
)

detector = RegexPIIDetector()

# --- Tag masking (default) ------------------------------------------------
anon_tag = Anonymizer(detector=detector, strategy=TagMaskingStrategy())
print(anon_tag.mask("My email is john@example.com"))
# My email is <EMAIL>

print(anon_tag.mask("Call me at 555-123-4567 or 192.168.1.1"))
# Call me at <PHONE> or <IPV4>

# --- [REDACTED] masking ---------------------------------------------------
anon_redacted = Anonymizer(detector=detector, strategy=RedactedMaskingStrategy())
print(anon_redacted.mask("My SSN is 123-45-6789"))
# My SSN is [REDACTED]

# --- Star masking (partial, keep first and last char) --------------------
anon_star = Anonymizer(
    detector=detector,
    strategy=StarMaskingStrategy(keep_start=1, keep_end=1),
)
print(anon_star.mask("Email: john@example.com"))
# Email: j**************m

# --- Batch masking --------------------------------------------------------
texts = [
    "Contact alice@corp.com for details",
    "The quarterly revenue grew by 12 percent",
    "Server 10.0.0.1 is down",
]
results = anon_tag.mask_batch(texts)
for original, masked in zip(texts, results):
    print(f"  {original!r:45s}  ->  {masked!r}")
