from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import config
from services.boundary import resolve_in_root
from services import runs


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _root_rel(path: Path) -> str:
    return path.resolve().relative_to(config.ROOT.resolve()).as_posix()


def _meta_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _heading_section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start: int | None = None
    target = heading.strip().lower()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and stripped[3:].strip().lower() == target:
            start = index + 1
            break
    if start is None:
        return []

    section: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("## "):
            break
        section.append(line)
    return section


def _clean_markdown(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^>\s?", "", cleaned)
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = cleaned.replace("`", "")
    return cleaned.strip()


def _section_text(lines: list[str]) -> str | None:
    cleaned = [_clean_markdown(line) for line in lines]
    cleaned = [line for line in cleaned if line]
    return "\n".join(cleaned) if cleaned else None


def _owner(text: str) -> str | None:
    raw = _meta_value(text, "Current owner") or _meta_value(text, "Owner")
    if not raw:
        return None
    lowered = raw.lower()
    if "codex" in lowered:
        return "codex"
    if "claude" in lowered:
        return "claude"
    return raw.strip().lower() or None


def _sub_systems(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in _heading_section(text, "Active sub-systems"):
        line = raw.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"sub-system", "subsystem"}:
            continue
        rows.append(
            {
                "name": _clean_markdown(cells[0]) or None,
                "status": _clean_markdown(cells[1]) or None,
                "note": _clean_markdown(cells[2]) or None,
            }
        )
    return rows


def _handoff_path(owner: str | None) -> Path | None:
    if owner != "claude":
        return None
    return config.OPUS_AI_DIR / "handoff-claude.md"


def _next_step(text: str) -> str | None:
    for heading in ("Exact next action", "Next step", "Task dang lam"):
        value = _section_text(_heading_section(text, heading))
        if value:
            return value
    return None


def _progress() -> dict[str, Any]:
    recent = runs.list_runs()[:20]
    latest = recent[0] if recent else None
    latest_run = None
    if latest is not None:
        latest_run = {
            "run_id": latest.get("run_id"),
            "suite": latest.get("suite") or latest.get("suite_name"),
            "status": latest.get("status"),
        }
    return {
        "latest_run": latest_run,
        "pass_count": sum(1 for run in recent if run.get("status") == "pass"),
        "fail_count": sum(1 for run in recent if run.get("status") == "fail"),
    }


def task_board() -> dict[str, Any]:
    source_files: list[str] = []
    status_path = config.OPUS_AI_DIR / "status.md"
    status_text = ""
    try:
        status_path = resolve_in_root(status_path)
        if status_path.is_file():
            status_text = _read_text(status_path)
            source_files.append(_root_rel(status_path))
    except PermissionError:
        status_text = ""

    owner = _owner(status_text)
    handoff_text = ""
    handoff_path = _handoff_path(owner)
    if handoff_path is not None:
        try:
            handoff_path = resolve_in_root(handoff_path)
            if handoff_path.is_file():
                handoff_text = _read_text(handoff_path)
                source_files.append(_root_rel(handoff_path))
        except PermissionError:
            handoff_text = ""

    return {
        "objective": _section_text(_heading_section(status_text, "Current objective")),
        "owner": owner,
        "updated": _meta_value(status_text, "Updated"),
        "sub_systems": _sub_systems(status_text),
        "next_step": _next_step(handoff_text) or _next_step(status_text),
        "source_files": source_files,
        "progress": _progress(),
    }
