from __future__ import annotations

import datetime as dt
import json
import threading
import time
from pathlib import Path
from typing import Any

import config
from parsers import claude_sessions, codex_sessions, inspect_eval
from parsers.common import as_int, normalize_ts, usage_total
from services import pricing


CACHE_TTL_SECONDS = 30.0
_USAGE_CACHE: dict[str, Any] = {"expires": 0.0, "events": [], "warnings": [], "fingerprint": None}
_DISK_CACHE = config.HUB_DIR / ".cache" / "usage_files.json"
_LOCK = threading.RLock()


def _cache_key(path: Path) -> str:
    return str(path.resolve())


def _load_disk() -> dict[str, Any]:
    try:
        data = json.loads(_DISK_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"files": {}}
    if not isinstance(data, dict):
        return {"files": {}}
    files = data.get("files")
    if not isinstance(files, dict):
        return {"files": {}}
    return {"files": files}


def _save_disk(cache: dict[str, Any]) -> None:
    try:
        _DISK_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _DISK_CACHE.write_text(json.dumps(cache, sort_keys=True), encoding="utf-8")
    except OSError:
        pass


def _chat_usage_file() -> Path | None:
    # Config wins if it names the file explicitly (either as its own constant
    # or as a "chat" entry in USAGE_SOURCES); otherwise there is no configured
    # chat source yet and we skip cleanly (NFR-002) rather than guessing a
    # real on-disk default that could leak unrelated production data into
    # callers/tests that don't know about this source.
    configured = getattr(config, "CHAT_USAGE_FILE", None)
    if configured is None:
        sources = config.USAGE_SOURCES if isinstance(config.USAGE_SOURCES, dict) else {}
        configured = sources.get("chat")
    return Path(configured) if configured is not None else None


def _chat_paths() -> list[Path]:
    path = _chat_usage_file()
    return [path] if path is not None and path.exists() else []


def _chat_event(obj: dict[str, Any], path: Path) -> dict[str, Any]:
    input_tokens = as_int(obj.get("input_tokens"))
    output_tokens = as_int(obj.get("output_tokens"))
    cache_read_tokens = as_int(obj.get("cache_read_tokens"))
    cache_creation_tokens = as_int(obj.get("cache_creation_tokens"))
    total_tokens = obj.get("total_tokens")
    calls = obj.get("calls")
    return {
        "ts": normalize_ts(obj.get("ts"), path),
        "source": str(obj.get("source") or "chat"),
        "model": str(obj.get("model") or "unknown"),
        "session": obj.get("session"),
        "command": obj.get("command"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "total_tokens": as_int(total_tokens)
        if total_tokens is not None
        else usage_total(input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens),
        "calls": as_int(calls) if calls is not None else 1,
    }


def _chat_parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
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
                events.append(_chat_event(obj, path))
    except OSError as exc:
        warnings.append(f"{path}: {exc}")
    return events, warnings


class _ChatUsageParser:
    """Adapter matching the claude_sessions/codex_sessions/inspect_eval parser
    protocol (paths()/parse_file()) for the single chat_usage.jsonl source."""

    @staticmethod
    def paths() -> list[Path]:
        return _chat_paths()

    @staticmethod
    def parse_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
        return _chat_parse_file(path)


_chat_parser = _ChatUsageParser()


def _source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for parser in (claude_sessions, codex_sessions, inspect_eval, _chat_parser):
        for path in parser.paths():
            try:
                stat = path.stat()
            except OSError:
                continue
            records.append(
                {
                    "parser": parser,
                    "path": path,
                    "key": _cache_key(path),
                    "mtime_ns": stat.st_mtime_ns,
                    "size": stat.st_size,
                }
            )
    return records


def _source_signature(records: list[dict[str, Any]]) -> tuple[tuple[str, int, int], ...]:
    return tuple((str(item["key"]), int(item["mtime_ns"]), int(item["size"])) for item in records)


def _entry_is_current(entry: Any, mtime_ns: int, size: int) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get("mtime_ns") == mtime_ns
        and entry.get("size") == size
        and isinstance(entry.get("events"), list)
        and isinstance(entry.get("warnings"), list)
    )


def _collect_from_files(
    records: list[dict[str, Any]], cache: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], bool]:
    files = cache.setdefault("files", {})
    if not isinstance(files, dict):
        files = {}
        cache["files"] = files

    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    changed = False
    current_keys = {str(record["key"]) for record in records}

    stale_keys = [key for key in files if key not in current_keys]
    for key in stale_keys:
        del files[key]
        changed = True

    for record in records:
        parser = record["parser"]
        path = record["path"]
        key = str(record["key"])
        mtime_ns = int(record["mtime_ns"])
        size = int(record["size"])
        entry = files.get(key)

        if _entry_is_current(entry, mtime_ns, size):
            file_events = entry["events"]
            file_warnings = entry["warnings"]
        else:
            file_events, file_warnings = parser.parse_file(path)
            files[key] = {
                "mtime_ns": mtime_ns,
                "size": size,
                "events": file_events,
                "warnings": file_warnings,
            }
            changed = True

        events.extend(file_events)
        warnings.extend(file_warnings)

    events.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
    return events, warnings, changed


def _collect_all() -> tuple[list[dict[str, Any]], list[str]]:
    now = time.monotonic()
    with _LOCK:
        records = _source_records()
        fingerprint = _source_signature(records)
        if _USAGE_CACHE.get("expires", 0.0) > now and _USAGE_CACHE.get("fingerprint") == fingerprint:
            return list(_USAGE_CACHE.get("events", [])), list(_USAGE_CACHE.get("warnings", []))

        disk_cache = _load_disk()
        events, warnings, changed = _collect_from_files(records, disk_cache)
        if changed:
            _save_disk(disk_cache)

        _USAGE_CACHE.update(
            {"expires": now + CACHE_TTL_SECONDS, "events": events, "warnings": warnings, "fingerprint": fingerprint}
        )
        return list(events), list(warnings)


def warm() -> None:
    """Best-effort cache warm (call in a background thread at startup)."""
    try:
        _collect_all()
    except Exception:
        pass


def _parse_since(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def _event_dt(event: dict[str, Any]) -> dt.datetime | None:
    ts = event.get("ts")
    if not isinstance(ts, str) or not ts:
        return None
    try:
        parsed = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def _matches(event: dict[str, Any], filters: dict[str, str | None], since_dt: dt.datetime | None) -> bool:
    source = filters.get("source")
    model = filters.get("model")
    if source and event.get("source") != source:
        return False
    if model and event.get("model") != model:
        return False
    if since_dt is not None:
        event_time = _event_dt(event)
        if event_time is None or event_time < since_dt:
            return False
    return True


def collect_usage(filters: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    since_dt = _parse_since(filters.get("since"))
    events, _warnings = _collect_all()
    filtered = [event for event in events if _matches(event, filters, since_dt)]
    filtered.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
    return filtered


def warnings() -> list[str]:
    _events, parser_warnings = _collect_all()
    return parser_warnings


def _empty_totals() -> dict[str, int]:
    return {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _empty_rollup_totals() -> dict[str, int | float]:
    return {
        **_empty_totals(),
        "cache_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "non_cache_tokens": 0,
        "estimated_cost_usd": 0.0,
        "unpriced_tokens": 0,
    }


def _add_tokens(target: dict[str, Any], event: dict[str, Any]) -> None:
    input_tokens = int(event.get("input_tokens") or 0)
    output_tokens = int(event.get("output_tokens") or 0)
    cache_read_tokens = int(event.get("cache_read_tokens") or 0)
    cache_creation_tokens = int(event.get("cache_creation_tokens") or 0)
    cache_tokens = cache_read_tokens + cache_creation_tokens

    target["calls"] += int(event.get("calls") or 0)
    target["input_tokens"] += input_tokens
    target["output_tokens"] += output_tokens
    target["total_tokens"] += int(event.get("total_tokens") or 0)
    if "cache_tokens" in target:
        target["cache_tokens"] += cache_tokens
    if "cache_read_tokens" in target:
        target["cache_read_tokens"] += cache_read_tokens
    if "cache_creation_tokens" in target:
        target["cache_creation_tokens"] += cache_creation_tokens
    if "non_cache_tokens" in target:
        target["non_cache_tokens"] += input_tokens + output_tokens


def rollup(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_model: dict[str, dict[str, Any]] = {}
    by_day: dict[str, dict[str, Any]] = {}
    by_source: dict[str, dict[str, Any]] = {}
    totals = _empty_rollup_totals()

    for usage_event in events:
        model = str(usage_event.get("model") or "unknown")
        day = str(usage_event.get("ts") or "")[:10] or "unknown"
        source = str(usage_event.get("source") or "unknown")

        model_row = by_model.setdefault("model:" + model, {"model": model, **_empty_rollup_totals(), "estimated_cost_usd": 0.0, "unpriced_tokens": 0})
        day_row = by_day.setdefault("day:" + day, {"day": day, **_empty_rollup_totals(), "estimated_cost_usd": 0.0})
        source_row = by_source.setdefault("source:" + source, {"source": source, "calls": 0, "total_tokens": 0, "estimated_cost_usd": 0.0})

        event_cost = pricing.estimate_cost({"model": model, **usage_event})

        _add_tokens(model_row, usage_event)
        _add_tokens(day_row, usage_event)
        model_row["estimated_cost_usd"] += event_cost["estimated_cost_usd"]
        model_row["unpriced_tokens"] += event_cost["unpriced_tokens"]
        day_row["estimated_cost_usd"] += event_cost["estimated_cost_usd"]
        source_row["calls"] += int(usage_event.get("calls") or 0)
        source_row["total_tokens"] += int(usage_event.get("total_tokens") or 0)
        source_row["estimated_cost_usd"] += event_cost["estimated_cost_usd"]
        _add_tokens(totals, usage_event)
        totals["estimated_cost_usd"] += event_cost["estimated_cost_usd"]
        totals["unpriced_tokens"] += event_cost["unpriced_tokens"]

    return {
        "by_model": sorted(by_model.values(), key=lambda item: item["total_tokens"], reverse=True),
        "by_day": sorted(by_day.values(), key=lambda item: item["day"]),
        "by_source": sorted(by_source.values(), key=lambda item: item["total_tokens"], reverse=True),
        "totals": totals,
    }


def _provider_for_model(model: str) -> str | None:
    if model == "cli:claude":
        return "claude"
    if model == "cli:codex":
        return "codex"
    if model.startswith("nvidia/") or model in config.CHAT_MODELS:
        return "nvidia"
    return None


def _provider_rollup(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_provider: dict[str, dict[str, Any]] = {}
    calls = 0
    total_tokens = 0

    for usage_event in events:
        provider = _provider_for_model(str(usage_event.get("model") or ""))
        if provider is None:
            continue
        row = by_provider.setdefault("provider:" + provider, {"provider": provider, "calls": 0, "total_tokens": 0})
        event_calls = int(usage_event.get("calls") or 0)
        event_tokens = int(usage_event.get("total_tokens") or 0)
        row["calls"] += event_calls
        row["total_tokens"] += event_tokens
        calls += event_calls
        total_tokens += event_tokens

    return {
        "by_provider": sorted(by_provider.values(), key=lambda item: item["total_tokens"], reverse=True),
        "calls": calls,
        "total_tokens": total_tokens,
    }


def cockpit_stats() -> dict[str, Any]:
    events, _warnings = _collect_all()
    today = dt.datetime.now(dt.UTC).date()
    today_str = today.isoformat()
    week_start_str = (today - dt.timedelta(days=6)).isoformat()

    today_events = [item for item in events if str(item.get("ts") or "")[:10] == today_str]
    week_events = [item for item in events if week_start_str <= str(item.get("ts") or "")[:10] <= today_str]

    today_stats = _provider_rollup(today_events)
    week_stats = _provider_rollup(week_events)
    quota_warn_per_day = int(getattr(config, "QUOTA_WARN_PER_DAY", 200))
    for row in today_stats["by_provider"]:
        row["quota_pct"] = (
            round(row["calls"] / quota_warn_per_day * 100, 1)
            if quota_warn_per_day > 0
            else None
        )

    return {
        "today": today_stats,
        "week7d": week_stats,
        "quota_warn_per_day": quota_warn_per_day,
        "warn": bool(today_stats["calls"] > quota_warn_per_day),
        "providers_online": [],
    }
