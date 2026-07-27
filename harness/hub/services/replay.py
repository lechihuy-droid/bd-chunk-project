from __future__ import annotations

import hashlib
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import config
from parsers.common import file_ts, normalize_ts
from services import risk


@dataclass(frozen=True)
class SessionRecord:
    session: str
    source: str
    path: Path
    ts: str
    project: str | None


def _codex_roots() -> list[Path]:
    roots = config.USAGE_SOURCES.get("codex", [])
    if isinstance(roots, Path):
        return [roots]
    return [root for root in roots if isinstance(root, Path)]


def _claude_paths() -> Iterable[tuple[str, Path, str | None]]:
    root = config.USAGE_SOURCES.get("claude")
    if not isinstance(root, Path) or not root.exists():
        return []
    return (("claude", path, path.parent.name) for path in root.glob("*/*.jsonl"))


def _codex_paths() -> Iterable[tuple[str, Path, str | None]]:
    rows: list[tuple[str, Path, str | None]] = []
    for root in _codex_roots():
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            rows.append(("codex", path, _codex_project(path)))
    return rows


def _codex_project(path: Path) -> str | None:
    for obj in _iter_jsonl(path, limit=40):
        value = _find_string(obj, "cwd")
        if value:
            return value
    return None


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


def _json_arg(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _session_ts(source: str, path: Path) -> str:
    if source == "codex":
        match = re.search(r"rollout-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})", path.name)
        if match:
            date, hour, minute, second = match.groups()
            return f"{date}T{hour}:{minute}:{second}+00:00"
    for obj in _iter_jsonl(path, limit=20):
        ts = obj.get("timestamp") if isinstance(obj, dict) else None
        if isinstance(ts, str) and ts:
            return normalize_ts(ts, path)
    return file_ts(path)


def _iter_jsonl(path: Path, limit: int | None = None) -> Iterable[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle):
                if limit is not None and index >= limit:
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except OSError:
        return


def _records() -> dict[str, SessionRecord]:
    raw = list(_claude_paths()) + list(_codex_paths())
    stems: dict[str, int] = {}
    for _source, path, _project in raw:
        stems[path.stem] = stems.get(path.stem, 0) + 1

    records: dict[str, SessionRecord] = {}
    for source, path, project in raw:
        session = path.stem
        if stems[session] > 1:
            digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:8]
            session = f"{session}-{digest}"
        records[session] = SessionRecord(
            session=session,
            source=source,
            path=path,
            ts=_session_ts(source, path),
            project=project,
        )
    return records


def list_sessions() -> list[dict[str, Any]]:
    rows = [
        {
            "session": record.session,
            "source": record.source,
            "ts": record.ts,
            "project": record.project,
        }
        for record in _records().values()
    ]
    return sorted(rows, key=lambda item: str(item.get("ts") or ""), reverse=True)


def _blocks(content: Any) -> list[Any]:
    if isinstance(content, list):
        return content
    if content is None:
        return []
    return [content]


def _text_from_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("content"), str):
            return value["content"]
        if isinstance(value.get("message"), str):
            return value["message"]
    if isinstance(value, list):
        return "\n".join(part for part in (_text_from_content(item) for item in value) if part)
    return ""


def _summary(value: Any, limit: int = 1200) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = str(value)
    text = text.strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def _provenance(role: str, trust: str) -> dict[str, str]:
    return {"provenance_role": role, "trust": trust}


def _command_tier(input_data: Any) -> str | None:
    command = risk.command_from_input(input_data)
    if command is None:
        return None
    return risk.classify_command(command)


def _tool_call(name: str, input_data: Any) -> dict[str, Any]:
    row = {"name": name, "input": input_data, "tier": risk.classify_action(name, input_data)}
    command_tier = _command_tier(input_data)
    if command_tier is not None:
        row["command_tier"] = command_tier
    return row


def _parse_latency_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def _add_agent_latencies(agent: list[dict[str, Any]]) -> None:
    previous: dt.datetime | None = None
    for row in agent:
        latency: float | None = None
        current = _parse_latency_ts(row.get("ts"))
        if previous is not None and current is not None:
            delta = (current - previous).total_seconds()
            if 0 <= delta <= 3600:
                latency = round(delta, 3)
        row["latency_s"] = latency
        if current is not None:
            previous = current


def _outline_from_todos(ts: str, input_data: Any, outline: list[dict[str, Any]]) -> None:
    if not isinstance(input_data, dict):
        return
    todos = input_data.get("todos")
    if not isinstance(todos, list):
        return
    for todo in todos:
        if not isinstance(todo, dict):
            continue
        content = todo.get("content")
        if not isinstance(content, str) or not content:
            continue
        status = todo.get("status")
        prefix = f"{status}: " if isinstance(status, str) and status else ""
        outline.append({"ts": ts, "kind": "todo", "text": prefix + content, **_provenance("model", "trusted")})


def _outline_from_plan_args(ts: str, args: Any, outline: list[dict[str, Any]]) -> None:
    data = _json_arg(args)
    if not isinstance(data, dict):
        return
    plan = data.get("plan")
    if not isinstance(plan, list):
        return
    for item in plan:
        if not isinstance(item, dict):
            continue
        step = item.get("step")
        if not isinstance(step, str) or not step:
            continue
        status = item.get("status")
        prefix = f"{status}: " if isinstance(status, str) and status else ""
        outline.append({"ts": ts, "kind": "plan", "text": prefix + step, **_provenance("model", "trusted")})


def _claude_replay(record: SessionRecord) -> dict[str, Any]:
    outline: list[dict[str, Any]] = []
    agent: list[dict[str, Any]] = []
    monitor: list[dict[str, Any]] = []
    tool_names: dict[str, str] = {}
    tool_tiers: dict[str, str] = {}

    for obj in _iter_jsonl(record.path):
        ts = normalize_ts(obj.get("timestamp"), record.path)
        kind = obj.get("type")
        message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
        if kind == "assistant":
            texts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for block in _blocks(message.get("content")):
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    text = block.get("text")
                    if isinstance(text, str) and text:
                        texts.append(text)
                elif block_type == "tool_use":
                    name = block.get("name")
                    input_data = block.get("input")
                    tool_id = block.get("id")
                    if isinstance(name, str) and name:
                        tier = risk.classify_action(name, input_data)
                        if isinstance(tool_id, str):
                            tool_names[tool_id] = name
                            tool_tiers[tool_id] = tier
                        tool_calls.append(_tool_call(name, input_data))
                        if name.lower() in {"todowrite", "todo_write"}:
                            _outline_from_todos(ts, input_data, outline)
            if texts or tool_calls:
                agent.append(
                    {
                        "ts": ts,
                        "role": "assistant",
                        "text": "\n".join(texts),
                        "tool_calls": tool_calls,
                        **_provenance("model", "trusted"),
                    }
                )
        elif kind == "user":
            for block in _blocks(message.get("content")):
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                tool_id = block.get("tool_use_id")
                tool = tool_names.get(tool_id) if isinstance(tool_id, str) else None
                tier = tool_tiers.get(tool_id) if isinstance(tool_id, str) else risk.classify_tool(tool)
                monitor.append(
                    {
                        "ts": ts,
                        "kind": "error" if block.get("is_error") else "tool_result",
                        "tool": tool,
                        "tier": tier,
                        "summary": _summary(block.get("content")),
                        **_provenance("tool", "untrusted"),
                    }
                )
        elif kind == "file-history-snapshot":
            monitor.append(
                {
                    "ts": ts,
                    "kind": "file",
                    "tool": None,
                    "tier": risk.UNKNOWN,
                    "summary": "file history snapshot",
                    **_provenance("system", "trusted"),
                }
            )

    _add_agent_latencies(agent)
    return {"session": record.session, "source": record.source, "outline": outline, "agent": agent, "monitor": monitor}


def _codex_payload(obj: dict[str, Any]) -> dict[str, Any]:
    payload = obj.get("payload")
    return payload if isinstance(payload, dict) else {}


def _codex_ts(obj: dict[str, Any], path: Path) -> str:
    payload = _codex_payload(obj)
    ts = obj.get("timestamp") or payload.get("timestamp")
    return normalize_ts(ts, path)


def _codex_replay(record: SessionRecord) -> dict[str, Any]:
    outline: list[dict[str, Any]] = []
    agent: list[dict[str, Any]] = []
    monitor: list[dict[str, Any]] = []
    tool_names: dict[str, str] = {}
    tool_tiers: dict[str, str] = {}

    for obj in _iter_jsonl(record.path):
        ts = _codex_ts(obj, record.path)
        event_type = obj.get("type")
        payload = _codex_payload(obj)
        payload_type = payload.get("type")

        if event_type == "event_msg" and payload_type == "agent_message":
            text = payload.get("message")
            if isinstance(text, str) and text:
                agent.append(
                    {
                        "ts": ts,
                        "role": "assistant",
                        "text": text,
                        "tool_calls": [],
                        **_provenance("model", "trusted"),
                    }
                )
            continue

        if event_type != "response_item":
            continue

        if payload_type == "function_call":
            name = payload.get("name")
            call_id = payload.get("call_id") or payload.get("id")
            args = payload.get("arguments", payload.get("input"))
            if isinstance(name, str) and name:
                parsed_args = _json_arg(args)
                tier = risk.classify_action(name, parsed_args)
                if isinstance(call_id, str):
                    tool_names[call_id] = name
                    tool_tiers[call_id] = tier
                agent.append(
                    {
                        "ts": ts,
                        "role": "assistant",
                        "text": "",
                        "tool_calls": [_tool_call(name, parsed_args)],
                        **_provenance("model", "trusted"),
                    }
                )
                if name.endswith("update_plan") or name == "update_plan":
                    _outline_from_plan_args(ts, args, outline)
        elif payload_type == "function_call_output":
            call_id = payload.get("call_id")
            tool = tool_names.get(call_id) if isinstance(call_id, str) else None
            tier = tool_tiers.get(call_id) if isinstance(call_id, str) else risk.classify_tool(tool)
            output = payload.get("output")
            summary = _summary(output)
            is_error = "Exit code: 1" in summary or "Traceback" in summary
            monitor.append(
                {
                    "ts": ts,
                    "kind": "error" if is_error else "tool_result",
                    "tool": tool,
                    "tier": tier,
                    "summary": summary,
                    **_provenance("tool", "untrusted"),
                }
            )
        elif payload_type == "message":
            text = _text_from_content(payload.get("content"))
            if text:
                agent.append(
                    {
                        "ts": ts,
                        "role": "assistant",
                        "text": text,
                        "tool_calls": [],
                        **_provenance("model", "trusted"),
                    }
                )

    _add_agent_latencies(agent)
    return {"session": record.session, "source": record.source, "outline": outline, "agent": agent, "monitor": monitor}


def session_replay(session: str) -> dict[str, Any]:
    record = _records().get(session)
    if record is None:
        raise FileNotFoundError(f"Session not found: {session}")
    if record.source == "claude":
        return _claude_replay(record)
    return _codex_replay(record)
