"""
Hatch build hook — optional post-install model download.
Only triggered when ANONYPII_AUTO_DOWNLOAD=1 is set in the environment.
"""

from __future__ import annotations

import os
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        if os.environ.get("ANONYPII_AUTO_DOWNLOAD", "").lower() not in ("1", "true", "yes"):
            return
        try:
            from anonypii.models.downloader import ModelDownloader

            which = os.environ.get("ANONYPII_DOWNLOAD_MODELS", "all")
            downloader = ModelDownloader()
            if which == "all":
                downloader.download_all(show_progress=True)
            else:
                for name in which.split(","):
                    downloader.download(name.strip(), show_progress=True)
        except Exception as exc:
            print(
                f"[anonypii] Post-install model download failed: {exc}\n"
                "You can download models manually with:  anonypii download all",
                file=sys.stderr,
            )
