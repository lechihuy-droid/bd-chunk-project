from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import config
from parsers.common import as_int, event, normalize_ts


def _paths() -> list[Path]:
    root = config.USAGE_SOURCES.get("inspect")
    if not isinstance(root, Path) or not root.exists():
        return []
    return sorted(root.glob("*.eval"))


def paths() -> list[Path]:
    return _paths()


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _model_usage_items(model_usage: Any) -> list[tuple[str, Any]]:
    if isinstance(model_usage, dict):
        return [(str(model), usage) for model, usage in model_usage.items()]
    if isinstance(model_usage, list):
        items: list[tuple[str, Any]] = []
        for usage in model_usage:
            model = _get(usage, "model")
            if isinstance(model, str) and model:
                items.append((model, usage))
        return items
    model = _get(model_usage, "model")
    if isinstance(model, str) and model:
        return [(model, model_usage)]
    return []


def _usage_event(path: Path, model: str, usage: Any, command: str | None, ts: Any) -> dict[str, Any]:
    input_tokens = as_int(_get(usage, "input_tokens") or _get(usage, "prompt_tokens"))
    output_tokens = as_int(_get(usage, "output_tokens") or _get(usage, "completion_tokens"))
    cache_read_tokens = as_int(
        _get(usage, "cache_read_tokens")
        or _get(usage, "cache_read_input_tokens")
        or _get(usage, "cached_input_tokens")
    )
    cache_creation_tokens = as_int(_get(usage, "cache_creation_tokens") or _get(usage, "cache_creation_input_tokens"))
    if input_tokens == 0 and output_tokens == 0:
        input_tokens = as_int(_get(usage, "total_tokens"))
    return event(
        ts=normalize_ts(ts, path),
        source="inspect",
        model=model,
        session=path.name,
        command=command,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        calls=as_int(_get(usage, "calls") or _get(usage, "requests")) or 1,
    )


def _events_from_model_usage(path: Path, model_usage: Any, command: str | None, ts: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for model, usage in _model_usage_items(model_usage):
        events.append(_usage_event(path, model, usage, command, ts))
    return events


def _read_with_inspect_ai(path: Path) -> list[dict[str, Any]]:
    from inspect_ai.log import read_eval_log

    log = read_eval_log(str(path))
    stats = _get(log, "stats")
    model_usage = _get(stats, "model_usage")
    eval_info = _get(log, "eval")
    command = _get(eval_info, "task") or _get(eval_info, "task_id") or _get(eval_info, "name")
    ts = _get(eval_info, "created") or _get(eval_info, "started_at") or _get(stats, "started_at")
    return _events_from_model_usage(path, model_usage, command, ts)


def _find_model_usage(obj: Any) -> list[Any]:
    found: list[Any] = []
    if isinstance(obj, dict):
        value = obj.get("model_usage")
        if value is not None:
            found.append(value)
        for child in obj.values():
            found.extend(_find_model_usage(child))
    elif isinstance(obj, list):
        for child in obj:
            found.extend(_find_model_usage(child))
    return found


def _read_zip_json(path: Path) -> list[dict[str, Any]]:
    if not zipfile.is_zipfile(path):
        return []
    events: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".json"):
                continue
            try:
                data = json.loads(archive.read(name).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError):
                continue
            command = _get(_get(data, "eval", {}), "task") or _get(data, "task")
            ts = _get(_get(data, "eval", {}), "created") or _get(data, "created")
            for model_usage in _find_model_usage(data):
                events.extend(_events_from_model_usage(path, model_usage, command, ts))
    return events


def parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []

    try:
        events = _read_with_inspect_ai(path)
    except Exception as exc:
        try:
            events = _read_zip_json(path)
        except Exception as fallback_exc:
            warnings.append(f"{path}: {exc}; fallback failed: {fallback_exc}")
            return [], warnings
        if not events:
            warnings.append(f"{path}: {exc}; no fallback model_usage found")
            return [], warnings
    return events, warnings


def collect() -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []

    for path in paths():
        file_events, file_warnings = parse_file(path)
        events.extend(file_events)
        warnings.extend(file_warnings)

    return events, warnings
