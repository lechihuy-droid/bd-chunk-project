from __future__ import annotations

from pathlib import Path

import pytest

import config
from services.boundary import resolve_in_root


def test_resolve_in_root_allows_paths_inside_root() -> None:
    resolved = resolve_in_root("harness")
    assert resolved == (config.ROOT / "harness").resolve()


def test_resolve_in_root_rejects_traversal_outside_root() -> None:
    with pytest.raises(PermissionError):
        resolve_in_root(Path("..") / ".." / "windows")
