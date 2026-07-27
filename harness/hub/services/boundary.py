from __future__ import annotations

from pathlib import Path

import config


ROOT_RESOLVED = config.ROOT.resolve()


def _inside(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def resolve_in_root(p: str | Path, base: str | Path = config.ROOT) -> Path:
    base_path = Path(base).resolve()
    if not _inside(base_path, ROOT_RESOLVED):
        raise PermissionError(f"Base path is outside project root: {base_path}")

    candidate = Path(p)
    if not candidate.is_absolute():
        candidate = base_path / candidate
    resolved = candidate.resolve()

    if not _inside(resolved, base_path):
        raise PermissionError(f"Path is outside allowed root: {resolved}")
    return resolved
