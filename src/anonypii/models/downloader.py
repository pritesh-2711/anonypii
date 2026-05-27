"""
Model download and cache management for anonypii.

Models are cached under ~/.cache/anonypii/models/<model-name>/ by default.
The cache directory can be overridden via the ANONYPII_CACHE_DIR environment
variable.

Download uses huggingface_hub.snapshot_download, which is included in the
`anonypii[model]` optional dependency group.
"""

from __future__ import annotations

import os
from pathlib import Path

from anonypii.models.registry import ALL_MODEL_NAMES, DEFAULT_MODEL, REGISTRY, get_model_info


def default_cache_dir() -> Path:
    base = os.environ.get("ANONYPII_CACHE_DIR") or os.path.join(
        os.path.expanduser("~"), ".cache", "anonypii", "models"
    )
    return Path(base)


class ModelDownloader:
    """
    Manages downloading, caching, and cache-checking of anonypii models.

    Parameters
    ----------
    cache_dir:
        Root directory for cached models.
        Defaults to ~/.cache/anonypii/models/ (or $ANONYPII_CACHE_DIR).
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self.cache_dir: Path = Path(cache_dir) if cache_dir else default_cache_dir()

    def model_path(self, model_name: str) -> Path:
        """Return the expected local path for a model."""
        get_model_info(model_name)
        return self.cache_dir / model_name

    def is_cached(self, model_name: str) -> bool:
        """
        Return True if the model's required files are present in the cache.

        Checks for config.json and model.safetensors (or pytorch_model.bin)
        as a proxy for a complete download.
        """
        path = self.model_path(model_name)
        if not path.exists():
            return False
        has_config = (path / "config.json").exists()
        has_weights = (
            (path / "model.safetensors").exists()
            or (path / "pytorch_model.bin").exists()
        )
        has_label_mapping = (path / "label_mapping.json").exists()
        return has_config and has_weights and has_label_mapping

    def download(
        self,
        model_name: str,
        show_progress: bool = True,
        force: bool = False,
    ) -> Path:
        """
        Download a model from HuggingFace Hub to the local cache.

        Parameters
        ----------
        model_name:     One of the registered model names.
        show_progress:  Show tqdm download progress bar.
        force:          Re-download even if already cached.

        Returns
        -------
        Path to the downloaded model directory.
        """
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise ImportError(
                "huggingface_hub is required to download models. "
                "Install with:  pip install anonypii[model]"
            ) from exc

        info = get_model_info(model_name)
        target = self.model_path(model_name)

        if not force and self.is_cached(model_name):
            if show_progress:
                print(f"[anonypii] Model '{model_name}' already cached at {target}")
            return target

        if show_progress:
            print(f"[anonypii] Downloading '{model_name}' from {info.hf_repo} ...")

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        local_dir = snapshot_download(
            repo_id=info.hf_repo,
            local_dir=str(target),
            local_dir_use_symlinks=False,
        )

        if show_progress:
            print(f"[anonypii] '{model_name}' downloaded to {local_dir}")

        return Path(local_dir)

    def download_all(
        self,
        show_progress: bool = True,
        force: bool = False,
    ) -> dict[str, Path]:
        """
        Download all registered models.

        Returns
        -------
        Dict mapping model name → local path.
        """
        results: dict[str, Path] = {}
        for name in ALL_MODEL_NAMES:
            results[name] = self.download(name, show_progress=show_progress, force=force)
        return results

    def list_cached(self) -> list[str]:
        """Return the names of all models that are fully cached."""
        return [name for name in ALL_MODEL_NAMES if self.is_cached(name)]

    def list_missing(self) -> list[str]:
        """Return the names of all models that are NOT cached."""
        return [name for name in ALL_MODEL_NAMES if not self.is_cached(name)]


def postinstall_hook() -> None:
    """
    Entry-point called when anonypii is installed with pip install anonypii[models].
    Downloads all models unless ANONYPII_SKIP_DOWNLOAD=1 is set.
    """
    import sys

    if os.environ.get("ANONYPII_SKIP_DOWNLOAD", "").lower() in ("1", "true", "yes"):
        return

    which = os.environ.get("ANONYPII_DOWNLOAD_MODELS", "all")
    downloader = ModelDownloader()

    try:
        if which == "all":
            downloader.download_all(show_progress=True)
        else:
            for name in which.split(","):
                name = name.strip()
                if name in REGISTRY:
                    downloader.download(name, show_progress=True)
                else:
                    print(
                        f"[anonypii] Unknown model '{name}' in ANONYPII_DOWNLOAD_MODELS; "
                        f"valid names: {ALL_MODEL_NAMES}",
                        file=sys.stderr,
                    )
    except Exception as exc:
        print(
            f"[anonypii] Post-install model download failed: {exc}\n"
            f"Download manually with:  anonypii download all",
            file=sys.stderr,
        )
