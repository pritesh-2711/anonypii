"""
Model registry for anonypii.

Two models are registered, both released on HuggingFace Hub by Pritesh Jha:

  piibench-deberta-base
      Direct fine-tuned DeBERTa-v3-base on the corrected PIIBench preparation.
      Best overall performance: F1 0.6455 on 100,002-record full held-out split.
      Wins 54 of 82 fine entity types vs SC+H.

  piibench-deberta-sch
      Source-conditioned hierarchical DeBERTa.
      Best on 28 entity types (e.g. HTTP_COOKIE +0.394, DATE_TIME +0.042).
      F1 0.5894 overall.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelInfo:
    name: str
    hf_repo: str
    description: str
    full_test_f1: float
    full_test_precision: float
    full_test_recall: float


REGISTRY: dict[str, ModelInfo] = {
    "piibench-deberta-base": ModelInfo(
        name="piibench-deberta-base",
        hf_repo="Pritesh-2711/piibench-deberta-base",
        description=(
            "Direct fine-tuned DeBERTa-v3-base on corrected PIIBench. "
            "Strongest overall: F1 0.6455 on 100k-record full test split. "
            "Recommended default model."
        ),
        full_test_f1=0.6455,
        full_test_precision=0.6277,
        full_test_recall=0.6645,
    ),
    "piibench-deberta-sch": ModelInfo(
        name="piibench-deberta-sch",
        hf_repo="Pritesh-2711/piibench-deberta-sch",
        description=(
            "Source-conditioned hierarchical DeBERTa. "
            "F1 0.5894 overall; stronger on 28 entity types including "
            "HTTP_COOKIE, DATE_TIME, COUNTY, COORDINATE, PHONE_NUMBER, "
            "COMPANY_NAME, BLOOD_TYPE, STATE, and EDUCATION_LEVEL."
        ),
        full_test_f1=0.5894,
        full_test_precision=0.5560,
        full_test_recall=0.6270,
    ),
}

DEFAULT_MODEL = "piibench-deberta-base"
ALL_MODEL_NAMES: list[str] = list(REGISTRY.keys())


def get_model_info(name: str) -> ModelInfo:
    from anonypii.core.exceptions import ModelNotFoundError

    if name not in REGISTRY:
        raise ModelNotFoundError(name, ALL_MODEL_NAMES)
    return REGISTRY[name]
