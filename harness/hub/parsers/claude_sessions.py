from __future__ import annotations

import json
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import config
from parsers.common import as_int, event, normalize_ts


_SEEN_MESSAGE_IDS: ContextVar[set[str] | None] = ContextVar("_SEEN_MESSAGE_IDS", default=None)


def _paths() -> list[Path]:
    root = config.USAGE_SOURCES.get("claude")
    if not isinstance(root, Path) or not root.exists():
        return []
    return sorted(root.glob("*/*.jsonl"))


def paths() -> list[Path]:
    return _paths()


def _project_name(path: Path) -> str:
    return path.parent.name


def _usage_event(path: Path, obj: dict[str, Any]) -> dict[str, Any] | None:
    message = obj.get("message")
    if not isinstance(message, dict):
        return None
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None
    model = message.get("model")
    if not isinstance(model, str) or not model:
        return None

    input_tokens = as_int(usage.get("input_tokens"))
    output_tokens = as_int(usage.get("output_tokens"))
    cache_read_tokens = as_int(usage.get("cache_read_input_tokens"))
    cache_creation_tokens = as_int(usage.get("cache_creation_input_tokens"))
    return event(
        ts=normalize_ts(obj.get("timestamp"), path),
        source="claude",
        model=model,
        session=path.stem,
        command=_project_name(path),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
        calls=1,
    )


def parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_message_ids = _SEEN_MESSAGE_IDS.get()
    if seen_message_ids is None:
        seen_message_ids = set()

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
                if not isinstance(obj, dict) or obj.get("type") != "assistant":
                    continue
                message = obj.get("message")
                if not isinstance(message, dict):
                    continue
                message_id = message.get("id")
                if isinstance(message_id, str) and message_id:
                    if message_id in seen_message_ids:
                        continue
                    seen_message_ids.add(message_id)
                usage_event = _usage_event(path, obj)
                if usage_event is not None:
                    events.append(usage_event)
    except OSError as exc:
        warnings.append(f"{path}: {exc}")

    return events, warnings


def collect() -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []

    token = _SEEN_MESSAGE_IDS.set(set())
    try:
        for path in paths():
            file_events, file_warnings = parse_file(path)
            events.extend(file_events)
            warnings.extend(file_warnings)
    finally:
        _SEEN_MESSAGE_IDS.reset(token)

    return events, warnings
