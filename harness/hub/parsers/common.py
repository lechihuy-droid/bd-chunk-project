from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any


def as_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def file_ts(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.UTC).replace(microsecond=0).isoformat()


def normalize_ts(value: Any, fallback_path: Path) -> str:
    if isinstance(value, str) and value:
        text = value.strip()
        try:
            parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.UTC)
            return parsed.isoformat()
        except ValueError:
            return text
    return file_ts(fallback_path)


def usage_total(input_tokens: int, output_tokens: int, cache_read_tokens: int, cache_creation_tokens: int) -> int:
    return input_tokens + output_tokens + cache_read_tokens + cache_creation_tokens


def event(
    *,
    ts: str,
    source: str,
    model: str,
    session: str,
    command: str | None,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    calls: int = 1,
) -> dict[str, Any]:
    return {
        "ts": ts,
        "source": source,
        "model": model,
        "session": session,
        "command": command,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "total_tokens": usage_total(input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens),
        "calls": calls,
    }
