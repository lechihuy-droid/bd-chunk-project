from __future__ import annotations

import os
from pathlib import Path


def _patch_platformdirs() -> None:
    data_root = os.environ.get("OPUS_INSPECT_DATA_DIR")
    cache_root = os.environ.get("OPUS_INSPECT_CACHE_DIR")
    if not data_root and not cache_root:
        return

    import platformdirs

    def user_data_path(
        appname: str | None = None,
        appauthor: str | bool | None = None,
        version: str | None = None,
        roaming: bool = False,
        ensure_exists: bool = False,
        **kwargs: object,
    ) -> Path:
        del appauthor, roaming, kwargs
        path = Path(data_root or os.environ.get("LOCALAPPDATA", ".")) / (appname or "app")
        if version:
            path = path / version
        if ensure_exists:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def user_cache_path(
        appname: str | None = None,
        appauthor: str | bool | None = None,
        version: str | None = None,
        opinion: bool = True,
        ensure_exists: bool = False,
        **kwargs: object,
    ) -> Path:
        del appauthor, opinion, kwargs
        path = Path(cache_root or data_root or ".") / (appname or "app")
        if version:
            path = path / version
        if ensure_exists:
            path.mkdir(parents=True, exist_ok=True)
        return path

    platformdirs.user_data_path = user_data_path
    platformdirs.user_cache_path = user_cache_path


_patch_platformdirs()
