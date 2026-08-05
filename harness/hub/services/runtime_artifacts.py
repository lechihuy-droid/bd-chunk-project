from __future__ import annotations

import re
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import config
from services import boundary, runtime_state


_SAFE_NODE_ID = re.compile(r"[A-Za-z0-9_-]")
MAX_ARTIFACT_CONTENT_CHARS = 1_000_000


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


def register_file_artifact(run_id: str, node_id: str, path: Path) -> dict[str, int | str]:
    """Register a renderer-produced file without copying it into the runtime store."""
    runtime_state.validate_id("run", run_id)
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Artifact file not found: {resolved}")
    item: dict[str, int | str] = {
        "name": resolved.name,
        "path": str(resolved),
        "size": resolved.stat().st_size,
        "node": node_id,
    }
    state = runtime_state.read_run(run_id)
    existing = [value for value in state.get("artifacts", []) if isinstance(value, dict)]
    existing.append(item)
    runtime_state.update_run_state(run_id, {"artifacts": existing})
    return item


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
    state = runtime_state.read_run(run_id)
    registered = [dict(item) for item in state.get("artifacts", []) if isinstance(item, dict)]
    return items + registered


def read_artifact(run_id: str, name: str) -> str:
    runtime_state.validate_id("run", run_id)
    if "/" in name or "\\" in name or ".." in name:
        raise FileNotFoundError(f"Artifact not found: {name}")
    artifacts_dir = _artifacts_dir(run_id)
    path = _resolve_artifact_path(artifacts_dir, name)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact not found: {name}")
    return path.read_text(encoding="utf-8", errors="replace")


def _library_path() -> Path:
    candidate = config.RUNTIME_STORE_DIR / "artifacts.json"
    try:
        return boundary.resolve_in_root(candidate)
    except PermissionError:
        # Tests may redirect the runtime store outside the repository. Keep the
        # boundary resolver as the normal path and retain equivalent containment.
        root = config.RUNTIME_STORE_DIR.resolve()
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise PermissionError(f"Path is outside allowed root: {resolved}") from exc
        return resolved


def _load_library() -> list[dict[str, object]]:
    path = _library_path()
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Artifact store is invalid") from exc
    if not isinstance(value, list):
        raise ValueError("Artifact store is invalid")
    return value


def _write_library(items: list[dict[str, object]]) -> None:
    path = _library_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _public_artifact(item: dict[str, object], include_content: bool) -> dict[str, object]:
    versions = item.get("versions", [])
    result = {key: item[key] for key in ("id", "title", "created_at", "source")}
    result["versions"] = [
        {key: version[key] for key in ("version", "created_at") if key in version} | ({"content": version["content"]} if include_content else {})
        for version in versions if isinstance(version, dict)
    ]
    if result["versions"]:
        result["version"] = result["versions"][-1]["version"]
    return result


def list_library_artifacts() -> list[dict[str, object]]:
    return [_public_artifact(item, include_content=False) for item in _load_library()]


def read_library_artifact(artifact_id: str) -> dict[str, object]:
    for item in _load_library():
        if item.get("id") == artifact_id:
            return _public_artifact(item, include_content=True)
    raise FileNotFoundError(f"Artifact not found: {artifact_id}")


def save_library_artifact(artifact_id: str | None, title: str | None, content: str, source: str | None) -> dict[str, object]:
    if len(content) > MAX_ARTIFACT_CONTENT_CHARS:
        raise ValueError(f"content exceeds {MAX_ARTIFACT_CONTENT_CHARS} characters")
    if source not in {"chat", "workflow_run"}:
        raise ValueError("source must be 'chat' or 'workflow_run'")
    items = _load_library()
    now = _now()
    if artifact_id:
        for item in items:
            if item.get("id") != artifact_id:
                continue
            if title is not None:
                item["title"] = title
            versions = item.get("versions")
            if not isinstance(versions, list):
                raise ValueError("Artifact store is invalid")
            versions.append({"version": f"v{len(versions) + 1}", "created_at": now, "content": content})
            _write_library(items)
            return _public_artifact(item, include_content=True)
        raise FileNotFoundError(f"Artifact not found: {artifact_id}")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    artifact = {"id": str(uuid4()), "title": title.strip(), "created_at": now, "source": source, "versions": [{"version": "v1", "created_at": now, "content": content}]}
    items.append(artifact)
    _write_library(items)
    return _public_artifact(artifact, include_content=True)
