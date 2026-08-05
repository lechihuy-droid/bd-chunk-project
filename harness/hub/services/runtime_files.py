from __future__ import annotations

from pathlib import Path

import config
from services import runtime_state


def _dir(run_id: str) -> Path:
    runtime_state.run_dir(run_id)
    path = runtime_state.runtime_path("run", run_id, "files")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(run_id: str, name: str) -> Path:
    if not name or name in {".", ".."}:
        raise FileNotFoundError("File not found")
    root = _dir(run_id)
    candidate = (root / name).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"File path is outside run root: {name}") from exc
    return candidate


def list_files(run_id: str) -> list[dict[str, object]]:
    root = _dir(run_id)
    return [{"name": p.name, "size": p.stat().st_size, "updated_at": runtime_state.now_iso() if False else p.stat().st_mtime_ns}
            for p in sorted(root.iterdir(), key=lambda item: item.name.lower()) if p.is_file()]


def upload(run_id: str, name: str, content: bytes) -> dict[str, object]:
    if len(content) > config.RUNTIME_FILE_MAX_BYTES:
        raise ValueError("File exceeds size limit")
    root = _dir(run_id)
    used = sum(p.stat().st_size for p in root.iterdir() if p.is_file())
    target = _path(run_id, name)
    previous = target.stat().st_size if target.is_file() else 0
    if used - previous + len(content) > config.RUNTIME_FILES_MAX_BYTES:
        raise ValueError("Run files exceed size limit")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return {"name": target.name, "size": len(content), "updated_at": target.stat().st_mtime_ns}


def download(run_id: str, name: str) -> Path:
    path = _path(run_id, name)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {name}")
    return path


def delete(run_id: str, name: str) -> None:
    path = download(run_id, name)
    path.unlink()
