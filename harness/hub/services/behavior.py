from __future__ import annotations

import datetime as dt
import json
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any

import config
from parsers.codex_sessions import _model_from_obj as _codex_model_from_obj
from services import replay, risk, usage


CACHE_TTL_SECONDS = 30.0
_BEHAVIOR_CACHE: dict[str, Any] = {
    "expires": 0.0,
    "events": [],
    "warnings": [],
    "sessions": [],
    "entropy": [],
    "fingerprint": None,
}
_DISK_CACHE = config.HUB_DIR / ".cache" / "behavior_files.json"
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


def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def _latency_values(agent_ts: list[str]) -> list[float]:
    values: list[float] = []
    previous: dt.datetime | None = None
    for ts in agent_ts:
        current = _parse_ts(ts)
        if previous is not None and current is not None:
            delta = (current - previous).total_seconds()
            if 0 <= delta <= 3600:
                values.append(round(delta, 3))
        if current is not None:
            previous = current
    return values


def _tool_event(
    record: replay.SessionRecord,
    tool: str,
    model: str | None,
    ts: str,
    input_data: Any = None,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "tier": risk.classify_action(tool, input_data),
        "source": record.source,
        "model": model,
        "session": record.session,
        "ts": ts,
    }


def _action(tool: str | None, ts: str, input_data: Any = None, is_error: bool = False, tier: str | None = None) -> dict[str, Any]:
    name = tool or "unknown"
    return {
        "tool": name,
        "ts": ts,
        "tier": tier or risk.classify_action(name, input_data),
        "is_error": bool(is_error),
    }


def _entropy_summary(record: replay.SessionRecord, actions: list[dict[str, Any]]) -> dict[str, Any]:
    previous_tool: str | None = None
    reason_counts: Counter[str] = Counter()
    scored: list[dict[str, Any]] = []

    for item in actions:
        tool = str(item.get("tool") or "unknown")
        tier = str(item.get("tier") or risk.UNKNOWN)
        reasons: list[str] = []
        if previous_tool is not None and tool == previous_tool:
            reasons.append("repeat_tool")
        if tier in {"network", "destructive"}:
            reasons.append("high_tier")
        if item.get("is_error"):
            reasons.append("error")
        previous_tool = tool

        for reason in reasons:
            reason_counts[reason] += 1
        scored.append({**item, "violation": bool(reasons), "reasons": reasons})

    max_rate = 0.0
    if scored:
        window = max(1, min(int(config.ENTROPY_WINDOW), len(scored)))
        for index in range(0, len(scored) - window + 1):
            chunk = scored[index : index + window]
            rate = sum(1 for item in chunk if item["violation"]) / window
            if rate > max_rate:
                max_rate = rate

    top_reason = reason_counts.most_common(1)[0][0] if reason_counts else None
    return {
        "session": record.session,
        "source": record.source,
        "actions": len(scored),
        "max_violation_rate": round(max_rate, 6),
        "flagged": max_rate > float(config.ENTROPY_THRESHOLD),
        "top_reason": top_reason,
    }


def _session_stats(record: replay.SessionRecord, session_events: list[dict[str, Any]], agent_ts: list[str]) -> dict[str, Any]:
    tools = [str(event.get("tool") or "") for event in session_events if event.get("tool")]
    total = len(tools)
    max_consecutive = 0
    top_tool: str | None = None
    current_tool: str | None = None
    current_count = 0

    for tool in tools:
        if tool == current_tool:
            current_count += 1
        else:
            current_tool = tool
            current_count = 1
        if current_count > max_consecutive:
            max_consecutive = current_count
            top_tool = tool

    distinct = len(set(tools))
    repeat_ratio = 0.0 if total == 0 else 1 - (distinct / total)
    latencies = _latency_values(agent_ts)
    avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else None
    max_latency = max(latencies) if latencies else None

    return {
        "session": record.session,
        "source": record.source,
        "max_consecutive": max_consecutive,
        "max_consecutive_same_tool": max_consecutive,
        "top_tool": top_tool,
        "total_tool_calls": total,
        "repeat_ratio": round(repeat_ratio, 6),
        "loop_risk": max_consecutive >= int(config.LOOP_CONSECUTIVE_THRESHOLD),
        "avg_latency_s": avg_latency,
        "max_latency_s": max_latency,
    }


def _claude_session(record: replay.SessionRecord) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    agent_ts: list[str] = []
    actions: list[dict[str, Any]] = []
    current_model: str | None = None
    tool_names: dict[str, str] = {}
    tool_tiers: dict[str, str] = {}

    for obj in replay._iter_jsonl(record.path):
        ts = replay.normalize_ts(obj.get("timestamp"), record.path)
        if obj.get("type") == "user":
            message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            for block in replay._blocks(message.get("content")):
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                if not block.get("is_error"):
                    continue
                tool_id = block.get("tool_use_id")
                tool = tool_names.get(tool_id) if isinstance(tool_id, str) else None
                tier = tool_tiers.get(tool_id) if isinstance(tool_id, str) else None
                actions.append(_action(tool, ts, is_error=True, tier=tier))
            continue

        if obj.get("type") != "assistant":
            continue
        message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
        model = message.get("model")
        if isinstance(model, str) and model:
            current_model = model

        has_agent_row = False
        for block in replay._blocks(message.get("content")):
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text" and isinstance(block.get("text"), str) and block.get("text"):
                has_agent_row = True
            elif block_type == "tool_use":
                name = block.get("name")
                input_data = block.get("input")
                tool_id = block.get("id")
                if isinstance(name, str) and name:
                    has_agent_row = True
                    tier = risk.classify_action(name, input_data)
                    if isinstance(tool_id, str):
                        tool_names[tool_id] = name
                        tool_tiers[tool_id] = tier
                    events.append(_tool_event(record, name, current_model, ts, input_data))
                    actions.append(_action(name, ts, input_data, tier=tier))
        if has_agent_row:
            agent_ts.append(ts)

    final_model = current_model or "claude:unknown"
    for event in events:
        if not event.get("model"):
            event["model"] = final_model
    return events, agent_ts, actions


def _codex_session(record: replay.SessionRecord) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    agent_ts: list[str] = []
    actions: list[dict[str, Any]] = []
    current_model: str | None = None
    tool_names: dict[str, str] = {}
    tool_tiers: dict[str, str] = {}

    for obj in replay._iter_jsonl(record.path):
        if current_model is None:
            current_model = _codex_model_from_obj(obj)

        ts = replay._codex_ts(obj, record.path)
        event_type = obj.get("type")
        payload = replay._codex_payload(obj)
        payload_type = payload.get("type")

        if event_type == "event_msg" and payload_type == "agent_message":
            text = payload.get("message")
            if isinstance(text, str) and text:
                agent_ts.append(ts)
            continue

        if event_type != "response_item":
            continue

        if payload_type == "function_call":
            name = payload.get("name")
            call_id = payload.get("call_id") or payload.get("id")
            args = replay._json_arg(payload.get("arguments", payload.get("input")))
            if isinstance(name, str) and name:
                tier = risk.classify_action(name, args)
                if isinstance(call_id, str):
                    tool_names[call_id] = name
                    tool_tiers[call_id] = tier
                events.append(_tool_event(record, name, current_model, ts, args))
                actions.append(_action(name, ts, args, tier=tier))
                agent_ts.append(ts)
        elif payload_type == "function_call_output":
            call_id = payload.get("call_id")
            output = payload.get("output")
            summary = replay._summary(output)
            is_error = "Exit code: 1" in summary or "Traceback" in summary
            if is_error:
                tool = tool_names.get(call_id) if isinstance(call_id, str) else None
                tier = tool_tiers.get(call_id) if isinstance(call_id, str) else None
                actions.append(_action(tool, ts, is_error=True, tier=tier))
        elif payload_type == "message":
            text = replay._text_from_content(payload.get("content"))
            if text:
                agent_ts.append(ts)

    final_model = current_model or "codex:unknown"
    for event in events:
        if not event.get("model"):
            event["model"] = final_model
    return events, agent_ts, actions


def _analyze_record(record: replay.SessionRecord) -> dict[str, Any]:
    try:
        if record.source == "claude":
            session_events, agent_ts, actions = _claude_session(record)
        else:
            session_events, agent_ts, actions = _codex_session(record)
    except Exception as exc:
        return {"events": [], "session_stat": None, "entropy": None, "warning": f"{record.path}: {exc}"}
    return {
        "events": session_events,
        "session_stat": _session_stats(record, session_events, agent_ts),
        "entropy": _entropy_summary(record, actions),
        "warning": None,
    }


def _build() -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    sessions: list[dict[str, Any]] = []
    entropy: list[dict[str, Any]] = []

    for record in replay._records().values():
        result = _analyze_record(record)
        events.extend(result["events"])
        if result["session_stat"] is not None:
            sessions.append(result["session_stat"])
        if result["entropy"] is not None:
            entropy.append(result["entropy"])
        if result["warning"] is not None:
            warnings.append(result["warning"])

    events.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
    sessions.sort(
        key=lambda item: (
            bool(item.get("loop_risk")),
            int(item.get("max_consecutive") or 0),
            int(item.get("total_tool_calls") or 0),
            str(item.get("session") or ""),
        ),
        reverse=True,
    )
    entropy.sort(
        key=lambda item: (
            bool(item.get("flagged")),
            float(item.get("max_violation_rate") or 0),
            int(item.get("actions") or 0),
            str(item.get("session") or ""),
        ),
        reverse=True,
    )
    return events, warnings, sessions, entropy


def _source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in replay._records().values():
        try:
            stat = record.path.stat()
        except OSError:
            continue
        records.append(
            {
                "record": record,
                "key": _cache_key(record.path),
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
            }
        )
    return records


def _source_signature(records: list[dict[str, Any]]) -> tuple[tuple[str, int, int, str, str], ...]:
    return tuple(
        (
            str(item["key"]),
            int(item["mtime_ns"]),
            int(item["size"]),
            str(item["record"].source),
            str(item["record"].session),
        )
        for item in records
    )


def _entry_is_current(entry: Any, record: replay.SessionRecord, mtime_ns: int, size: int) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get("mtime_ns") == mtime_ns
        and entry.get("size") == size
        and entry.get("source") == record.source
        and entry.get("session") == record.session
        and isinstance(entry.get("events"), list)
        and (isinstance(entry.get("session_stat"), dict) or entry.get("session_stat") is None)
        and (isinstance(entry.get("entropy"), dict) or entry.get("entropy") is None)
        and (isinstance(entry.get("warning"), str) or entry.get("warning") is None)
    )


def _collect_from_files(
    records: list[dict[str, Any]], cache: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]], bool]:
    files = cache.setdefault("files", {})
    if not isinstance(files, dict):
        files = {}
        cache["files"] = files

    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    sessions: list[dict[str, Any]] = []
    entropy: list[dict[str, Any]] = []
    changed = False
    current_keys = {str(record["key"]) for record in records}

    stale_keys = [key for key in files if key not in current_keys]
    for key in stale_keys:
        del files[key]
        changed = True

    for item in records:
        record = item["record"]
        key = str(item["key"])
        mtime_ns = int(item["mtime_ns"])
        size = int(item["size"])
        entry = files.get(key)

        if _entry_is_current(entry, record, mtime_ns, size):
            result = entry
        else:
            result = _analyze_record(record)
            files[key] = {
                "mtime_ns": mtime_ns,
                "size": size,
                "source": record.source,
                "session": record.session,
                "events": result["events"],
                "session_stat": result["session_stat"],
                "entropy": result["entropy"],
                "warning": result["warning"],
            }
            changed = True

        events.extend(result["events"])
        if result["session_stat"] is not None:
            sessions.append(result["session_stat"])
        if result["entropy"] is not None:
            entropy.append(result["entropy"])
        if result["warning"] is not None:
            warnings.append(result["warning"])

    events.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
    sessions.sort(
        key=lambda item: (
            bool(item.get("loop_risk")),
            int(item.get("max_consecutive") or 0),
            int(item.get("total_tool_calls") or 0),
            str(item.get("session") or ""),
        ),
        reverse=True,
    )
    entropy.sort(
        key=lambda item: (
            bool(item.get("flagged")),
            float(item.get("max_violation_rate") or 0),
            int(item.get("actions") or 0),
            str(item.get("session") or ""),
        ),
        reverse=True,
    )
    return events, warnings, sessions, entropy, changed


def _collect_all() -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    now = time.monotonic()
    with _LOCK:
        records = _source_records()
        fingerprint = _source_signature(records)
        if _BEHAVIOR_CACHE["expires"] > now and _BEHAVIOR_CACHE["fingerprint"] == fingerprint:
            return (
                list(_BEHAVIOR_CACHE["events"]),
                list(_BEHAVIOR_CACHE["warnings"]),
                list(_BEHAVIOR_CACHE["sessions"]),
                list(_BEHAVIOR_CACHE["entropy"]),
            )

        disk_cache = _load_disk()
        events, warnings, sessions, entropy, changed = _collect_from_files(records, disk_cache)
        if changed:
            _save_disk(disk_cache)

        _BEHAVIOR_CACHE.update(
            {
                "expires": now + CACHE_TTL_SECONDS,
                "events": events,
                "warnings": warnings,
                "sessions": sessions,
                "entropy": entropy,
                "fingerprint": fingerprint,
            }
        )
        return list(events), list(warnings), list(sessions), list(entropy)


def warm() -> None:
    """Best-effort cache warm (call in a background thread at startup)."""
    try:
        _collect_all()
    except Exception:
        pass


def collect_tool_events() -> tuple[list[dict[str, Any]], list[str]]:
    events, warnings, _sessions, _entropy = _collect_all()
    return events, warnings


def _matches(event: dict[str, Any], filters: dict[str, str | None], since_dt: dt.datetime | None) -> bool:
    source = filters.get("source")
    model = filters.get("model")
    if source and event.get("source") != source:
        return False
    if model and event.get("model") != model:
        return False
    if since_dt is not None:
        event_time = usage._event_dt(event)
        if event_time is None or event_time < since_dt:
            return False
    return True


def filter_tool_events(
    events: list[dict[str, Any]],
    filters: dict[str, str | None] | None = None,
) -> list[dict[str, Any]]:
    filters = filters or {}
    since_dt = usage._parse_since(filters.get("since"))
    filtered = [event for event in events if _matches(event, filters, since_dt)]
    filtered.sort(key=lambda item: str(item.get("ts") or ""), reverse=True)
    return filtered


def tool_rollup(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_tool: dict[str, dict[str, Any]] = {}
    by_day: dict[str, dict[str, Any]] = {}

    for event in events:
        tool = str(event.get("tool") or "unknown")
        day = str(event.get("ts") or "")[:10] or "unknown"
        model = str(event.get("model") or "unknown")
        session = str(event.get("session") or "")

        tool_row = by_tool.setdefault(
            tool,
            {"tool": tool, "tier": risk.classify_tool(tool), "count": 0, "_sessions": set(), "_models": set()},
        )
        day_row = by_day.setdefault(day, {"day": day, "count": 0})
        tool_row["count"] += 1
        if session:
            tool_row["_sessions"].add(session)
        if model:
            tool_row["_models"].add(model)
        day_row["count"] += 1

    tool_rows = [
        {
            "tool": row["tool"],
            "tier": row["tier"],
            "count": row["count"],
            "sessions": len(row["_sessions"]),
            "models": sorted(row["_models"]),
        }
        for row in by_tool.values()
    ]

    return {
        "by_tool": sorted(tool_rows, key=lambda item: (-int(item["count"]), str(item["tool"]))),
        "by_day": sorted(by_day.values(), key=lambda item: item["day"]),
        "totals": {"tool_calls": len(events), "distinct_tools": len(by_tool)},
    }


def session_loops() -> list[dict[str, Any]]:
    _events, _warnings, sessions, _entropy = _collect_all()
    return sessions


def session_entropy() -> list[dict[str, Any]]:
    _events, _warnings, _sessions, entropy = _collect_all()
    return entropy
