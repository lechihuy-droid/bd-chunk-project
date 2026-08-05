from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import config
from services import boundary


def _path() -> Path:
    return boundary.resolve_in_root(config.RUNTIME_STORE_DIR / "artifact_comments.json", config.RUNTIME_STORE_DIR)


def _load() -> list[dict[str, object]]:
    path = _path()
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Comment store is invalid")
    return [item for item in value if isinstance(item, dict)]


def _write(items: list[dict[str, object]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def list_comments(artifact_id: str) -> list[dict[str, object]]:
    return [item for item in _load() if item.get("artifact_id") == artifact_id]


def create(artifact_id: str, quoted_text: str, author: str, body: str) -> dict[str, object]:
    if not quoted_text.strip() or not author.strip() or not body.strip():
        raise ValueError("quoted_text, author and body are required")
    item: dict[str, object] = {
        "id": str(uuid4()), "artifact_id": artifact_id, "quoted_text": quoted_text.strip(),
        "author": author.strip(), "body": body.strip(),
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"), "resolved": False,
    }
    items = _load(); items.append(item); _write(items)
    return item


def resolve(artifact_id: str, comment_id: str, resolved: bool) -> dict[str, object]:
    items = _load()
    for item in items:
        if item.get("artifact_id") == artifact_id and item.get("id") == comment_id:
            item["resolved"] = resolved; _write(items); return item
    raise FileNotFoundError("Comment not found")


def delete(artifact_id: str, comment_id: str) -> None:
    items = _load()
    retained = [item for item in items if not (item.get("artifact_id") == artifact_id and item.get("id") == comment_id)]
    if len(retained) == len(items):
        raise FileNotFoundError("Comment not found")
    _write(retained)
