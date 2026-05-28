"""
Model-backed PII detector using fine-tuned DeBERTa models from HuggingFace Hub.

Wraps the inference logic derived from the original pii-bench codebase and
exposes it through the PIIDetector interface.

Two models are supported:

  "piibench-deberta-base"  — direct fine-tuned DeBERTa (recommended default)
  "piibench-deberta-sch"   — source-conditioned hierarchical DeBERTa

Both require the anonypii[model] extras to be installed (torch, transformers,
huggingface_hub, sentencepiece, accelerate).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from anonypii.core.entities import Entity, EntityType
from anonypii.core.exceptions import (
    ModelInferenceError,
    ModelLoadError,
    ModelNotDownloadedError,
)
from anonypii.detectors.base import OverlapPolicy, PIIDetector
from anonypii.models.downloader import ModelDownloader
from anonypii.models.registry import DEFAULT_MODEL, get_model_info

# Maximum characters per text — avoids silent truncation on huge inputs
_MAX_CHARS = 50_000

# Required files that must be present in a cached model directory
_REQUIRED_FILES = {"config.json", "label_mapping.json"}


class ModelPIIDetector(PIIDetector):
    """
    DeBERTa-based PII detector.

    Parameters
    ----------
    model:
        Model name.  One of "piibench-deberta-base" (default) or
        "piibench-deberta-sch".
    download:
        If True, automatically download the model when it is not cached.
        If False (default), raises ModelNotDownloadedError when not cached.
    cache_dir:
        Override the local model cache directory.
    confidence_threshold:
        Global minimum confidence for an entity to be included.
        Default 0.5.
    max_length:
        Maximum tokenized sequence length.  Default 256.
    device:
        "cuda", "cpu", or None (auto-select).
    batch_size:
        Batch size for batched inference in detect_batch().
    active_entity_types:
        Restrict detection to a subset of entity types.
    confidence_thresholds:
        Per-entity-type confidence overrides.
    allowlist:
        Literal strings or compiled regexes to suppress from results.
    overlap_policy:
        How to resolve overlapping spans.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        download: bool = False,
        cache_dir: str | Path | None = None,
        confidence_threshold: float = 0.5,
        max_length: int = 256,
        device: str | None = None,
        batch_size: int = 32,
        active_entity_types: set[EntityType] | None = None,
        confidence_thresholds: dict[EntityType, float] | None = None,
        allowlist: list[str | re.Pattern[str]] | None = None,
        overlap_policy: OverlapPolicy = OverlapPolicy.LONGEST_SPAN,
    ) -> None:
        super().__init__(
            active_entity_types=active_entity_types,
            confidence_threshold=confidence_threshold,
            confidence_thresholds=confidence_thresholds,
            allowlist=allowlist,
            overlap_policy=overlap_policy,
        )

        info = get_model_info(model)
        self._model_name = model
        self._hf_repo = info.hf_repo
        self.max_length = max_length
        self.batch_size = batch_size

        downloader = ModelDownloader(cache_dir=cache_dir)
        model_path = downloader.model_path(model)

        if not downloader.is_cached(model):
            if download:
                model_path = downloader.download(model, show_progress=True)
            else:
                raise ModelNotDownloadedError(model, str(downloader.cache_dir))

        self._model_path = model_path
        self._id2label, self._label2id = self._load_label_mapping()
        self._tokenizer, self._model, self._device = self._load_model(device)
        self._source_conditioned: bool = self._detect_source_conditioned()
        self._default_source_token: str = "[SRC=general]"

    # ------------------------------------------------------------------
    # Detector interface
    # ------------------------------------------------------------------

    def _detect_raw(self, text: str) -> list[Entity]:
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]
        try:
            return self._run_inference(text)
        except Exception as exc:
            raise ModelInferenceError(str(exc)) from exc

    def detect_batch(self, texts: list[str]) -> list[Any]:
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_results = self._run_batch(batch)
            results.extend(batch_results)
        return results

    # ------------------------------------------------------------------
    # Internal: model loading
    # ------------------------------------------------------------------

    def _load_label_mapping(self) -> tuple[dict[int, str], dict[str, int]]:
        mapping_path = self._model_path / "label_mapping.json"
        try:
            with open(mapping_path, encoding="utf-8") as f:
                mapping = json.load(f)
            id2label = {int(k): v for k, v in mapping["id2label"].items()}
            label2id: dict[str, int] = mapping["label2id"]
            return id2label, label2id
        except Exception as exc:
            raise ModelLoadError(
                self._model_name, f"Cannot read label_mapping.json: {exc}"
            ) from exc

    def _load_model(self, device: str | None) -> tuple[Any, Any, Any]:
        try:
            import torch
            from transformers import AutoConfig

            config = AutoConfig.from_pretrained(str(self._model_path))
            architecture = getattr(config, "pii_model_architecture", "flat")

            tok = self._load_tokenizer()

            if architecture == "hierarchical":
                model = self._load_hierarchical_model(config)
            else:
                from transformers import AutoModelForTokenClassification

                model = AutoModelForTokenClassification.from_pretrained(str(self._model_path))

            dev = torch.device(
                device if device else ("cuda" if torch.cuda.is_available() else "cpu")
            )
            model.to(dev)
            model.eval()
            return tok, model, dev
        except (ModelLoadError, ModelNotDownloadedError):
            raise
        except Exception as exc:
            raise ModelLoadError(self._model_name, str(exc)) from exc

    def _load_tokenizer(self) -> Any:
        from transformers import AutoTokenizer

        try:
            return AutoTokenizer.from_pretrained(str(self._model_path))
        except AttributeError as exc:
            if "'list' object has no attribute 'keys'" not in str(exc):
                raise
            return AutoTokenizer.from_pretrained(str(self._model_path), extra_special_tokens={})

    def _load_hierarchical_model(self, config: Any) -> Any:
        try:
            import sys

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from anonypii._compat.train_novel import (
                COARSE_NAMES,
                HierarchicalPIIModel,
            )

            return HierarchicalPIIModel.from_pretrained(
                str(self._model_path),
                config=config,
                num_fine_labels=len(self._label2id),
                num_coarse_labels=len(COARSE_NAMES),
                coarse_weight=float(getattr(config, "pii_coarse_loss_weight", 0.3)),
            )
        except Exception as exc:
            raise ModelLoadError(
                self._model_name,
                f"Hierarchical model loading failed: {exc}",
            ) from exc

    def _detect_source_conditioned(self) -> bool:
        try:
            from transformers import AutoConfig

            cfg = AutoConfig.from_pretrained(str(self._model_path))
            return bool(getattr(cfg, "pii_source_conditioned", False))
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal: inference
    # ------------------------------------------------------------------

    def _prepare_text(self, text: str) -> tuple[str, int]:
        if not self._source_conditioned:
            return text, 0
        prefix = f"{self._default_source_token} "
        return prefix + text, len(prefix)

    def _run_inference(self, text: str) -> list[Entity]:
        import torch

        model_text, offset_shift = self._prepare_text(text)
        encoding = self._tokenizer(
            model_text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_offsets_mapping=True,
        )
        raw_offsets: list[tuple[int, int]] = encoding.pop("offset_mapping")[0].tolist()
        offset_mapping = self._shift_offsets(raw_offsets, offset_shift)
        encoding = {k: v.to(self._device) for k, v in encoding.items()}

        with torch.inference_mode():
            logits = self._model(**encoding).logits
            probs = torch.softmax(logits, dim=-1)[0]
            pred_ids = torch.argmax(probs, dim=-1).cpu().numpy()
            confidences = probs.max(dim=-1).values.cpu().numpy()

        return self._extract_entities(text, pred_ids, confidences, offset_mapping)

    def _run_batch(self, texts: list[str]) -> list[Any]:
        import torch

        from anonypii.core.result import DetectionResult

        prepared = [self._prepare_text(t) for t in texts]
        model_texts = [p[0] for p in prepared]
        offsets_shifts = [p[1] for p in prepared]

        encoding = self._tokenizer(
            model_texts,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,
            return_offsets_mapping=True,
        )
        raw_offsets_batch = encoding.pop("offset_mapping").tolist()
        encoding = {k: v.to(self._device) for k, v in encoding.items()}

        with torch.inference_mode():
            logits = self._model(**encoding).logits
            probs = torch.softmax(logits, dim=-1)

        results = []
        for j, (text, raw_offsets, shift) in enumerate(
            zip(texts, raw_offsets_batch, offsets_shifts, strict=True)
        ):
            offset_mapping = self._shift_offsets(raw_offsets, shift)
            pred_ids = torch.argmax(probs[j], dim=-1).cpu().numpy()
            confs = probs[j].max(dim=-1).values.cpu().numpy()
            entities_raw = self._extract_entities(text, pred_ids, confs, offset_mapping)
            filtered = self._filter(entities_raw)
            from anonypii.detectors.base import _resolve_overlaps

            resolved = _resolve_overlaps(filtered, self.overlap_policy)
            sorted_entities = tuple(sorted(resolved, key=lambda e: e.start))
            results.append(DetectionResult(text=text, entities=sorted_entities))
        return results

    def _shift_offsets(
        self,
        offsets: list[tuple[int, int]],
        shift: int,
    ) -> list[tuple[int, int]]:
        if shift == 0:
            return offsets
        shifted = []
        for cs, ce in offsets:
            if cs == 0 and ce == 0 or ce <= shift:
                shifted.append((0, 0))
            else:
                shifted.append((max(0, cs - shift), max(0, ce - shift)))
        return shifted

    def _extract_entities(
        self,
        text: str,
        pred_ids: Any,
        confidences: Any,
        offset_mapping: list[tuple[int, int]],
    ) -> list[Entity]:
        entities: list[Entity] = []
        current_type: str | None = None
        current_start: int | None = None
        current_end: int | None = None
        current_confs: list[float] = []

        for pred_id, conf, (char_start, char_end) in zip(
            pred_ids, confidences, offset_mapping, strict=False
        ):
            if char_start == 0 and char_end == 0:
                continue

            label = self._id2label.get(int(pred_id), "O")
            if float(conf) < self.confidence_threshold:
                label = "O"

            if label.startswith("B-"):
                if current_type is not None:
                    entities.append(
                        self._make_entity(
                            text, current_type, current_start, current_end, current_confs
                        )
                    )
                current_type = label[2:]
                current_start = char_start
                current_end = char_end
                current_confs = [float(conf)]

            elif label.startswith("I-") and current_type == label[2:]:
                current_end = char_end
                current_confs.append(float(conf))

            else:
                if current_type is not None:
                    entities.append(
                        self._make_entity(
                            text, current_type, current_start, current_end, current_confs
                        )
                    )
                current_type = None
                current_start = None
                current_end = None
                current_confs = []

        if current_type is not None:
            entities.append(
                self._make_entity(text, current_type, current_start, current_end, current_confs)
            )

        return entities

    def _make_entity(
        self,
        text: str,
        etype: str,
        start: int | None,
        end: int | None,
        confs: list[float],
    ) -> Entity:
        import numpy as np

        assert start is not None and end is not None
        try:
            entity_type = EntityType(etype)
        except ValueError:
            entity_type = EntityType.MISC

        return Entity(
            text=text[start:end],
            type=entity_type,
            start=start,
            end=end,
            confidence=float(np.mean(confs)),
        )
