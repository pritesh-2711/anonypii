"""
Using the fine-tuned DeBERTa models for full 82-type PII detection.

Requires: pip install anonypii[model]
Models must be downloaded first:  anonypii download all

Or with auto-download at runtime:
    ModelPIIDetector(model="piibench-deberta-base", download=True)
"""

from anonypii import Anonymizer, ReversibleAnonymizer
from anonypii.core.entities import EntityType
from anonypii.detectors.model import ModelPIIDetector
from anonypii.models.downloader import ModelDownloader
from anonypii.models.registry import REGISTRY

# --- Show available models -----------------------------------------------
print("Available models:")
for name, info in REGISTRY.items():
    print(f"  {name}")
    print(f"    F1={info.full_test_f1:.4f}  {info.description[:70]}")
print()

# --- Check download status -----------------------------------------------
downloader = ModelDownloader()
print("Cached models   :", downloader.list_cached())
print("Missing models  :", downloader.list_missing())
print()

# --- Using piibench-deberta-base (recommended) ---------------------------
# Uncomment once downloaded:
#
# detector = ModelPIIDetector(
#     model="piibench-deberta-base",
#     confidence_threshold=0.5,
# )
#
# result = detector.detect(
#     "My name is Alice Johnson and my email is alice@example.com"
# )
# print("Entities detected:")
# for entity in result.entities:
#     print(f"  [{entity.type.value}] {entity.text!r}  conf={entity.confidence:.3f}")
#
# --- Full anonymize + restore pipeline with the model --------------------
#
# anon = Anonymizer(model="piibench-deberta-base", confidence_threshold=0.5)
# result = anon.anonymize("Wire $5000 to IBAN GB29NWBK60161331926819")
# print("Anonymized:", result.text)
# print("Restored  :", result.restore())
#
# --- Per-entity-type confidence thresholds --------------------------------
#
# from anonypii.core.entities import EntityType
# detector_tuned = ModelPIIDetector(
#     model="piibench-deberta-base",
#     confidence_threshold=0.5,
#     confidence_thresholds={
#         EntityType.SSN: 0.9,       # require very high confidence for SSN
#         EntityType.PERSON: 0.6,    # slightly higher for names
#     },
# )
#
# --- Using the SC+H model (stronger on 28 types) -------------------------
#
# detector_sch = ModelPIIDetector(
#     model="piibench-deberta-sch",
#     confidence_threshold=0.5,
# )
# # SC+H is stronger for: HTTP_COOKIE, DATE_TIME, COUNTY, COORDINATE,
# # PHONE_NUMBER, COMPANY_NAME, BLOOD_TYPE, STATE, EDUCATION_LEVEL
# result_sch = detector_sch.detect(
#     "Set-Cookie: session=abc123; Expires=Wed, 09 Jun 2025 10:18:14 GMT"
# )
# print("SC+H entities:", [(e.type.value, e.text) for e in result_sch.entities])

print("Uncomment the code above after downloading models.")
print("Run:  anonypii download all")
