from __future__ import annotations

import re
from pathlib import Path

from services import boundary, runtime_state


_SAFE_NODE_ID = re.compile(r"[A-Za-z0-9_-]")


def _artifacts_dir(run_id: str):
    return runtime_state.runtime_path("run", run_id, "artifacts")


def _resolve_artifact_path(artifacts_dir: Path, name: str) -> Path:
    try:
        return boundary.resolve_in_root(artifacts_dir / name, artifacts_dir)
    except PermissionError:
        # Test/runtime roots may be outside the project root; retain the same
        # containment check when boundary resolver cannot accept that base.
        resolved = (artifacts_dir / name).resolve()
        try:
            resolved.relative_to(artifacts_dir.resolve())
        except ValueError as exc:
            raise PermissionError(f"Path is outside allowed root: {resolved}") from exc
        return resolved


def write_node_artifact(run_id: str, node_id: str, text: str) -> str:
    artifacts_dir = _artifacts_dir(run_id)
    safe_node_id = "".join(char if _SAFE_NODE_ID.fullmatch(char) else "_" for char in node_id)
    path = _resolve_artifact_path(artifacts_dir, f"{safe_node_id}.md")
    path.write_text(text, encoding="utf-8")
    return f"artifacts/{safe_node_id}.md"


def list_artifacts(run_id: str) -> list[dict[str, int | str]]:
    runtime_state.validate_id("run", run_id)
    artifacts_dir = _artifacts_dir(run_id)
    if not artifacts_dir.is_dir():
        return []
    items: list[dict[str, int | str]] = []
    for path in sorted(artifacts_dir.glob("*.md"), key=lambda item: item.name):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            items.append({"name": path.name, "chars": len(text)})
    return items


def read_artifact(run_id: str, name: str) -> str:
    runtime_state.validate_id("run", run_id)
    if "/" in name or "\\" in name or ".." in name:
        raise FileNotFoundError(f"Artifact not found: {name}")
    artifacts_dir = _artifacts_dir(run_id)
    path = _resolve_artifact_path(artifacts_dir, name)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact not found: {name}")
    return path.read_text(encoding="utf-8", errors="replace")
