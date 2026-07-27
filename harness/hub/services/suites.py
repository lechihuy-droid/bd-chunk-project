from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config
from services.boundary import resolve_in_root


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _root_rel(path: Path) -> str:
    return path.resolve().relative_to(config.ROOT.resolve()).as_posix()


def _check(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    return {
        "id": raw.get("id"),
        "type": raw.get("type"),
        "hint": raw.get("hint", ""),
        "raw": raw,
    }


def _suite(path: Path) -> dict[str, Any]:
    resolved = resolve_in_root(path, config.SUITES_DIR)
    data = _read_json(resolved)
    checks = [_check(item) for item in data.get("checks", []) if _check(item) is not None]
    return {
        "id": data.get("id") or resolved.stem,
        "name": data.get("name") or data.get("id") or resolved.stem,
        "description": data.get("description", ""),
        "checks": checks,
        "check_count": len(checks),
        "path": _root_rel(resolved),
    }


def list_suites() -> list[dict[str, Any]]:
    if not config.SUITES_DIR.exists():
        return []

    suites: list[dict[str, Any]] = []
    for path in config.SUITES_DIR.rglob("*.json"):
        try:
            suites.append(_suite(path))
        except (OSError, ValueError, PermissionError, json.JSONDecodeError):
            continue
    return sorted(suites, key=lambda item: str(item.get("id") or ""))


def get_suite(suite_id: str) -> dict[str, Any]:
    for suite in list_suites():
        if suite["id"] == suite_id:
            return suite
    raise FileNotFoundError(f"Suite not found: {suite_id}")
