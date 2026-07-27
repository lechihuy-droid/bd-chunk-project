from __future__ import annotations

import json
import uuid
from typing import Any, Iterator

from services import runtime_state


def append_event(run_id: str, event_type: str, data: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
    run_id = runtime_state.validate_id("run", run_id)
    runtime_state.run_dir(run_id)
    event = {
        "event_id": f"event-{runtime_state.now_iso().replace(':', '').replace('-', '')}-{uuid.uuid4().hex[:8]}",
        "type": str(event_type),
        "run_id": run_id,
        "ts": runtime_state.now_iso(),
    }
    if data:
        event.update(data)
    if fields:
        event.update(fields)
    path = runtime_state.runtime_path("run", run_id, "events.jsonl")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_events(run_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    runtime_state.validate_id("run", run_id)
    runtime_state.run_dir(run_id)
    path = runtime_state.runtime_path("run", run_id, "events.jsonl")
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                events.append(item)
    if limit is not None and limit >= 0:
        return events[-limit:]
    return events


def to_sse(event: dict[str, Any]) -> str:
    event_type = str(event.get("type") or "message")
    return f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


def replay_sse(run_id: str) -> Iterator[str]:
    for event in read_events(run_id):
        yield to_sse(event)
