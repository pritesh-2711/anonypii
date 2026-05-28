"""
anonypii CLI

Commands:

  anonypii detect   <text|-f file>          Detect and print PII entities
  anonypii mask     <text|-f file>          Mask PII (irreversible)
  anonypii anonymize <text|-f file>         Anonymize PII (reversible, saves mapping)
  anonypii restore  <text|-f file>          Restore anonymized text from mapping
  anonypii download [model|all]             Download model weights
  anonypii info                             Show cached models and config
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _print_err(msg: str) -> None:
    print(f"[anonypii] ERROR: {msg}", file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anonypii",
        description="PII detection, masking, and reversible anonymization.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------
    # detect
    # ------------------------------------------------------------------
    detect_p = sub.add_parser("detect", help="Detect PII entities in text")
    detect_p.add_argument("text", nargs="?", help="Input text (or use -f)")
    detect_p.add_argument("-f", "--file", help="Input text file (one text per line)")
    detect_p.add_argument("--model", default="piibench-deberta-base")
    detect_p.add_argument("--download", action="store_true")
    detect_p.add_argument("--config", help="Entity config YAML/JSON path")
    detect_p.add_argument("--threshold", type=float, default=0.5)
    detect_p.add_argument("--json", action="store_true", help="Output JSON")

    # ------------------------------------------------------------------
    # mask
    # ------------------------------------------------------------------
    mask_p = sub.add_parser("mask", help="Mask PII in text (irreversible)")
    mask_p.add_argument("text", nargs="?")
    mask_p.add_argument("-f", "--file")
    mask_p.add_argument("--model", default="piibench-deberta-base")
    mask_p.add_argument("--download", action="store_true")
    mask_p.add_argument("--config", help="Entity config YAML/JSON path")
    mask_p.add_argument("--threshold", type=float, default=0.5)
    mask_p.add_argument(
        "--strategy",
        choices=["tag", "redacted", "star"],
        default="tag",
        help="Masking strategy (default: tag)",
    )
    mask_p.add_argument("-o", "--output", help="Write output to file")

    # ------------------------------------------------------------------
    # anonymize
    # ------------------------------------------------------------------
    anon_p = sub.add_parser("anonymize", help="Anonymize PII in text (reversible)")
    anon_p.add_argument("text", nargs="?")
    anon_p.add_argument("-f", "--file")
    anon_p.add_argument("--model", default="piibench-deberta-base")
    anon_p.add_argument("--download", action="store_true")
    anon_p.add_argument("--config", help="Entity config YAML/JSON path")
    anon_p.add_argument("--threshold", type=float, default=0.5)
    anon_p.add_argument("--output-mapping", help="Save mapping to JSON file")
    anon_p.add_argument("-o", "--output", help="Write anonymized text to file")

    # ------------------------------------------------------------------
    # restore
    # ------------------------------------------------------------------
    restore_p = sub.add_parser("restore", help="Restore anonymized text from mapping")
    restore_p.add_argument("text", nargs="?")
    restore_p.add_argument("-f", "--file")
    restore_p.add_argument("--mapping", required=True, help="Mapping JSON file")
    restore_p.add_argument("-o", "--output", help="Write restored text to file")

    # ------------------------------------------------------------------
    # download
    # ------------------------------------------------------------------
    dl_p = sub.add_parser("download", help="Download model weights")
    dl_p.add_argument(
        "model",
        nargs="?",
        default="all",
        help=(
            "Model to download: 'piibench-deberta-base', 'piibench-deberta-sch', "
            "or 'all' (default: all)"
        ),
    )
    dl_p.add_argument("--cache-dir", help="Override cache directory")
    dl_p.add_argument("--force", action="store_true", help="Re-download even if cached")

    # ------------------------------------------------------------------
    # info
    # ------------------------------------------------------------------
    sub.add_parser("info", help="Show cached models and config")

    return parser


def _build_anonymizer(args: argparse.Namespace):
    from anonypii.core.anonymizer import Anonymizer
    from anonypii.masking.strategies import (
        RedactedMaskingStrategy,
        StarMaskingStrategy,
        TagMaskingStrategy,
    )

    strategy_map = {
        "tag": TagMaskingStrategy(),
        "redacted": RedactedMaskingStrategy(),
        "star": StarMaskingStrategy(),
    }
    strategy = strategy_map.get(getattr(args, "strategy", "tag"), TagMaskingStrategy())

    return Anonymizer(
        model=args.model,
        download=args.download,
        strategy=strategy,
        config_path=getattr(args, "config", None),
        confidence_threshold=args.threshold,
    )


def _get_texts(args: argparse.Namespace) -> list[str]:
    if getattr(args, "file", None):
        return [
            line.rstrip("\n") for line in Path(args.file).open(encoding="utf-8") if line.strip()
        ]
    if getattr(args, "text", None):
        return [args.text]
    text = sys.stdin.read().strip()
    if text:
        return [text]
    _print_err("No input text provided. Use a positional argument, -f FILE, or stdin.")
    sys.exit(1)


def _cmd_detect(args: argparse.Namespace) -> None:
    anon = _build_anonymizer(args)
    texts = _get_texts(args)
    for text in texts:
        result = anon._detector.detect(text)
        if getattr(args, "json", False):
            print(result.to_json())
        else:
            if result.has_pii:
                for entity in result.entities:
                    print(
                        f"[{entity.type.value}] {entity.text!r}  "
                        f"({entity.start}:{entity.end}, conf={entity.confidence:.2f})"
                    )
            else:
                print("No PII detected.")


def _cmd_mask(args: argparse.Namespace) -> None:
    anon = _build_anonymizer(args)
    texts = _get_texts(args)
    lines = [anon.mask(t) for t in texts]
    output = "\n".join(lines)
    if getattr(args, "output", None):
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


def _cmd_anonymize(args: argparse.Namespace) -> None:
    anon = _build_anonymizer(args)
    texts = _get_texts(args)
    combined_mapping: dict[str, str] = {}
    output_lines: list[str] = []

    for text in texts:
        result = anon.anonymize(text)
        output_lines.append(result.text)
        combined_mapping.update(result.mapping)

    output = "\n".join(output_lines)
    if getattr(args, "output", None):
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    if getattr(args, "output_mapping", None):
        Path(args.output_mapping).write_text(
            json.dumps(combined_mapping, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[anonypii] Mapping saved -> {args.output_mapping}", file=sys.stderr)


def _cmd_restore(args: argparse.Namespace) -> None:
    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    texts = _get_texts(args)
    lines = []
    for text in texts:
        result = text
        for token, original in mapping.items():
            result = result.replace(token, original)
        lines.append(result)

    output = "\n".join(lines)
    if getattr(args, "output", None):
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


def _cmd_download(args: argparse.Namespace) -> None:
    from anonypii.models.downloader import ModelDownloader
    from anonypii.models.registry import ALL_MODEL_NAMES

    downloader = ModelDownloader(cache_dir=getattr(args, "cache_dir", None))
    model = args.model

    if model == "all":
        downloader.download_all(show_progress=True, force=args.force)
    elif model in ALL_MODEL_NAMES:
        downloader.download(model, show_progress=True, force=args.force)
    else:
        _print_err(f"Unknown model '{model}'. Valid: {ALL_MODEL_NAMES} or 'all'")
        sys.exit(1)


def _cmd_info(_args: argparse.Namespace) -> None:
    from anonypii.models.downloader import ModelDownloader
    from anonypii.models.registry import REGISTRY

    downloader = ModelDownloader()
    cached = downloader.list_cached()
    missing = downloader.list_missing()

    print(f"Cache directory: {downloader.cache_dir}")
    print()
    print("Registered models:")
    for name, info in REGISTRY.items():
        status = "cached" if name in cached else "NOT CACHED"
        print(f"  [{status}] {name}")
        print(f"           {info.hf_repo}")
        print(f"           F1={info.full_test_f1:.4f}  {info.description[:70]}")
    if missing:
        print()
        print("To download missing models:  anonypii download all")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    command_map = {
        "detect": _cmd_detect,
        "mask": _cmd_mask,
        "anonymize": _cmd_anonymize,
        "restore": _cmd_restore,
        "download": _cmd_download,
        "info": _cmd_info,
    }

    try:
        command_map[args.command](args)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        _print_err(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
