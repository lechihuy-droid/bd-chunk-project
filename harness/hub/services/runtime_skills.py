from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from services import runtime_state, skill_library


_SLUG_RE = re.compile(r"[^a-z0-9._-]+")
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:-]*$")


def _id(name: str) -> str:
    return _SLUG_RE.sub("-", name.lower()).strip("-")


def _summary(content: str) -> tuple[str, str, str]:
    """Preserve the legacy runtime title/description fallbacks."""
    meta, body = skill_library.split_frontmatter(content)
    title = description = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip() or title
        else:
            description = stripped
            break
    return meta.get("name", ""), title, description


def _records(include_body: bool = False) -> list[dict[str, Any]]:
    """Read the authoritative library and adapt it to the legacy API shape."""
    rows: dict[str, dict[str, Any]] = {}
    for entry in skill_library.list_skills():
        fallback_name = str(entry["id"]).partition("/")[2]
        detail = skill_library.get_skill(str(entry["id"]))
        content = str(detail["content"])
        declared, heading, first_line = _summary(content)
        name = declared if _NAME_RE.match(declared) else fallback_name
        skill_id = _id(name)
        if not skill_id or skill_id in rows:
            continue
        path = Path(str(entry["path"]))
        rows[skill_id] = {
            "id": skill_id,
            "title": name if declared and _NAME_RE.match(declared) else heading or name or "Untitled skill",
            "description": str(entry["description"]).strip() or first_line,
            "path": str(path / "SKILL.md") if path.is_dir() else str(path),
            "read_only": True,
            **({"body": content} if include_body else {}),
        }
    return sorted(rows.values(), key=lambda row: str(row["id"]))


def list_skills() -> list[dict[str, Any]]:
    return _records()


def get_skill(skill_id: str) -> dict[str, Any]:
    for record in _records(include_body=True):
        if record["id"] == skill_id:
            return record
    raise FileNotFoundError(f"Skill not found: {skill_id}")


def skill_usage(skill_id: str) -> dict[str, Any]:
    get_skill(skill_id)
    path = runtime_state.runtime_path("store", "", "skill_usage.jsonl")
    rows: list[dict[str, Any]] = []
    if path.is_file():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict) and item.get("skill_id") == skill_id:
                    rows.append(item)
    return {"skill_id": skill_id, "count": len(rows), "events": rows[-50:]}
