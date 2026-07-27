from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import config
from services import runtime_state
from services.skill_library import split_frontmatter


_SLUG_RE = re.compile(r"[^a-z0-9._-]+")
# A frontmatter `name:` is only trusted when it looks like a skill name; a
# malformed block can otherwise leak YAML punctuation into the id.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:-]*$")


def _skill_roots() -> list[Path]:
    """Roots the Skills page lists: the configured skill sources, nothing else.

    Deliberately excludes vendored plugin caches (~/.codex/plugins/cache) — those
    are bundled copies the user does not author or deploy, and they ship the same
    skill under several version directories.
    """
    return [Path(path) for path in config.SKILL_SOURCES.values()]


def _fallback_id(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"skill-{digest}"


def _dir_name(path: Path) -> str:
    return path.parent.name if path.name.lower() == "skill.md" else path.stem


def _summary(body: str) -> tuple[str, str]:
    """Fall back to the markdown body for skills without frontmatter."""
    title = ""
    description = ""
    for line in body.splitlines():
        stripped = line.strip()
        # A leftover `---` means the frontmatter block never closed; skip it
        # rather than surfacing the delimiter as the description.
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip() or title
            continue
        description = stripped
        break
    return title, description


def _is_hidden(path: Path, root: Path) -> bool:
    """True for skills tucked under a dot-directory (e.g. `.codex/skills/.system`)."""
    return any(part.startswith(".") for part in path.relative_to(root).parts[:-1])


def _iter_skill_files() -> list[Path]:
    files: list[Path] = []
    for root in _skill_roots():
        if not root.exists():
            continue
        try:
            files.extend(
                path
                for path in root.rglob("SKILL.md")
                if path.is_file() and not _is_hidden(path, root)
            )
        except OSError:
            continue
    return sorted(files, key=lambda path: str(path).lower())


def _skill_record(path: Path, include_body: bool = False) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = split_frontmatter(text)
    declared = meta.get("name", "").strip()
    if not _NAME_RE.match(declared):
        declared = ""
    name = declared or _dir_name(path)
    heading, first_line = _summary(body)
    record: dict[str, Any] = {
        "id": _SLUG_RE.sub("-", name.lower()).strip("-") or _fallback_id(path),
        "title": declared or heading or name or "Untitled skill",
        "description": meta.get("description", "").strip() or first_line,
        "path": str(path),
        "read_only": True,
    }
    if include_body:
        record["body"] = text
    return record


def list_skills() -> list[dict[str, Any]]:
    """One row per skill; the first path wins when an id repeats.

    Repeats happen when the same skill is present in two sources, or when a root
    keeps several version directories of it (`26.715.31925/` and `latest/`).
    """
    rows: dict[str, dict[str, Any]] = {}
    for path in _iter_skill_files():
        try:
            record = _skill_record(path)
        except OSError:
            continue
        rows.setdefault(record["id"], record)
    return sorted(rows.values(), key=lambda row: str(row["id"]))


def get_skill(skill_id: str) -> dict[str, Any]:
    for path in _iter_skill_files():
        try:
            record = _skill_record(path, include_body=True)
        except OSError:
            continue
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
