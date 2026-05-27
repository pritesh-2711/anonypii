"""
Reversible anonymization: anonymize text then restore the original.
"""

from anonypii import Anonymizer, Deanonymizer, ReversibleAnonymizer
from anonypii.detectors.regex import RegexPIIDetector
from anonypii.masking.strategies import TokenMaskingStrategy
from anonypii.masking.token_generator import HashTokenGenerator
from anonypii.vault.json_file import JsonFileVault
from anonypii.vault.memory import InMemoryVault

detector = RegexPIIDetector()

# --- Stateless: Anonymizer returns result with mapping -------------------
anon = Anonymizer(
    detector=detector,
    reversible_strategy=TokenMaskingStrategy(),
)
result = anon.anonymize("My email is john@example.com and SSN is 123-45-6789")
print("Anonymized :", result.text)
print("Mapping    :", result.mapping)
print("Restored   :", result.restore())
print()

# --- Stateful: ReversibleAnonymizer keeps vault across calls -------------
ra = ReversibleAnonymizer(detector=detector, vault=InMemoryVault())
r1 = ra.anonymize("Contact alice@corp.com")
r2 = ra.anonymize("SSN on file: 123-45-6789")
print("Anon 1:", r1.text)
print("Anon 2:", r2.text)
print("Restore 1:", ra.restore(r1.text))
print("Restore 2:", ra.restore(r2.text))
print()

# --- Deanonymizer: separate anonymize + restore processes ----------------
anon2 = Anonymizer(
    detector=detector,
    reversible_strategy=TokenMaskingStrategy(),
)
deano = Deanonymizer()
original = "Reach bob@example.com for details"
result2 = anon2.anonymize(original)
deano.load_mapping(result2.mapping)
print("Deanonymized:", deano.restore_from_vault(result2.text))
print()

# --- HashTokenGenerator: deterministic across sessions -------------------
salt = b"my-app-secret"
anon3 = Anonymizer(
    detector=detector,
    reversible_strategy=TokenMaskingStrategy(generator=HashTokenGenerator(salt=salt)),
)
r_a = anon3.anonymize("Email: carol@example.com")
r_b = anon3.anonymize("Email: carol@example.com")
print("Same input, same token:", r_a.text == r_b.text)

# --- Persistent vault with JsonFileVault ---------------------------------
import tempfile, pathlib

with tempfile.TemporaryDirectory() as tmpdir:
    vault_path = pathlib.Path(tmpdir) / "vault.json"
    ra_persistent = ReversibleAnonymizer(
        detector=detector,
        vault=JsonFileVault(vault_path),
    )
    result_p = ra_persistent.anonymize("dave@example.com")
    print("Vault file exists:", vault_path.exists())
    # In a second process, load the vault and restore:
    restore_vault = JsonFileVault(vault_path)
    print("Restored from file vault:", restore_vault.restore_text(result_p.text))
