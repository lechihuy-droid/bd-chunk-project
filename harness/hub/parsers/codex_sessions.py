from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import config
from parsers.common import as_int, event, file_ts


def _paths() -> list[Path]:
    roots = config.USAGE_SOURCES.get("codex", [])
    if isinstance(roots, Path):
        roots = [roots]
    paths: list[Path] = []
    for root in roots:
        if isinstance(root, Path) and root.exists():
            paths.extend(root.rglob("*.jsonl"))
    return sorted(paths)


def paths() -> list[Path]:
    return _paths()


def _rollout_ts(path: Path) -> str:
    match = re.search(r"rollout-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})", path.name)
    if match:
        date, hour, minute, second = match.groups()
        return f"{date}T{hour}:{minute}:{second}+00:00"
    return file_ts(path)


def _find_string(obj: Any, key: str) -> str | None:
    if isinstance(obj, dict):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
        for child in obj.values():
            found = _find_string(child, key)
            if found:
                return found
    elif isinstance(obj, list):
        for child in obj:
            found = _find_string(child, key)
            if found:
                return found
    return None


def _model_from_obj(obj: dict[str, Any]) -> str | None:
    direct = obj.get("model")
    if isinstance(direct, str) and direct:
        return direct
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return None
    for key in ("model", "model_slug"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    collaboration_mode = payload.get("collaboration_mode")
    if isinstance(collaboration_mode, dict):
        settings = collaboration_mode.get("settings")
        if isinstance(settings, dict):
            value = settings.get("model")
            if isinstance(value, str) and value:
                return value
    return None


def _token_payload(obj: dict[str, Any]) -> dict[str, Any] | None:
    if obj.get("type") == "token_count":
        return obj
    payload = obj.get("payload")
    if isinstance(payload, dict) and payload.get("type") == "token_count":
        return payload
    return None


def _usage_from_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    info = payload.get("info")
    candidates: list[Any] = [
        payload.get("token_usage"),
        payload.get("usage"),
    ]
    if isinstance(info, dict):
        candidates.extend(
            [
                info.get("total_token_usage"),
                info.get("token_usage"),
                info.get("last_token_usage"),
            ]
        )
    for candidate in candidates:
        if isinstance(candidate, dict) and (
            "input_tokens" in candidate or "output_tokens" in candidate or "total_tokens" in candidate
        ):
            return candidate
    return None


def _cache_read(usage: dict[str, Any]) -> int:
    return as_int(
        usage.get("cache_read_tokens")
        or usage.get("cache_read_input_tokens")
        or usage.get("cached_input_tokens")
    )


def _cache_creation(usage: dict[str, Any]) -> int:
    return as_int(usage.get("cache_creation_tokens") or usage.get("cache_creation_input_tokens"))


def _usage_event(path: Path, model: str, command: str | None, calls: int, usage: dict[str, Any]) -> dict[str, Any]:
    return event(
        ts=_rollout_ts(path),
        source="codex",
        model=model or "codex:unknown",
        session=path.stem,
        command=command,
        input_tokens=as_int(usage.get("input_tokens") or usage.get("prompt_tokens")),
        output_tokens=as_int(usage.get("output_tokens") or usage.get("completion_tokens")),
        cache_read_tokens=_cache_read(usage),
        cache_creation_tokens=_cache_creation(usage),
        calls=calls,
    )


def parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    model: str | None = None
    command: str | None = None
    calls = 0
    last_usage: dict[str, Any] | None = None

    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError as exc:
                    warnings.append(f"{path}: line {line_number}: {exc}")
                    continue
                if not isinstance(obj, dict):
                    continue
                if model is None:
                    model = _model_from_obj(obj)
                if command is None:
                    command = _find_string(obj, "cwd")
                payload = _token_payload(obj)
                if payload is None:
                    continue
                calls += 1
                usage = _usage_from_payload(payload)
                if usage is not None:
                    last_usage = usage
    except OSError as exc:
        warnings.append(f"{path}: {exc}")
        return events, warnings

    if calls and last_usage is None:
        warnings.append(f"{path}: token_count events found without token usage")
        return events, warnings
    if last_usage is not None:
        events.append(_usage_event(path, model or "codex:unknown", command, calls, last_usage))

    return events, warnings


def collect() -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []

    for path in paths():
        file_events, file_warnings = parse_file(path)
        events.extend(file_events)
        warnings.extend(file_warnings)

    return events, warnings
