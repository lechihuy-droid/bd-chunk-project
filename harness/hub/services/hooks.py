from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path
from typing import Any

import config
from services import gitjobs, runtime_state


_FILE = config.RUNTIME_STORE_DIR / "hooks.json"
_LOG = config.RUNTIME_STORE_DIR / "hook-log.jsonl"
_LOCK = threading.Lock()
_EVENTS = ("state_snapshot", "error", "warning", "child_run", "validation_fail", "validation_pass", "node_update", "assistant_delta", "reasoning", "tool_call", "tool_result", "artifact_written", "done")


def _read() -> list[dict[str, Any]]:
    try:
        value = json.loads(_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write(rows: list[dict[str, Any]]) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def events() -> list[str]: return list(_EVENTS)
def list_hooks() -> list[dict[str, Any]]: return _read()

def _validate(payload: dict[str, Any], old: dict[str, Any] | None = None) -> dict[str, Any]:
    row = dict(old or {}) | dict(payload)
    if not isinstance(row.get("name"), str) or not row["name"].strip(): raise ValueError("name is required")
    if not isinstance(row.get("agent_id"), str) or not row["agent_id"].strip(): raise ValueError("agent_id is required")
    if row.get("event") not in _EVENTS: raise ValueError("event must be a runtime event")
    if not isinstance(row.get("trigger_point"), str): raise ValueError("trigger_point is required")
    if not isinstance(row.get("enabled"), bool): raise ValueError("enabled must be boolean")
    action = row.get("action")
    if not isinstance(action, dict) or action.get("type") not in {"webhook", "append_log_file", "shell"}: raise ValueError("action must be webhook, append_log_file or shell")
    if action["type"] == "shell":
        command = action.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command): raise ValueError("action.command must be a non-empty command array")
        return row
    key = "url" if action["type"] == "webhook" else "path"
    if not isinstance(action.get(key), str) or not action[key]: raise ValueError(f"action.{key} is required")
    return row


def create(payload: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        row = _validate(payload); row["id"] = runtime_state.new_id("run").replace("run-", "hook-")
        row.update({"executed_count": 0, "last_run_at": None, "last_status": None})
        rows = _read(); rows.append(row); _write(rows); return row


def update(hook_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        rows = _read()
        for index, old in enumerate(rows):
            if old.get("id") == hook_id:
                row = _validate(payload, old); row["id"] = hook_id; rows[index] = row; _write(rows); return row
    raise FileNotFoundError(f"Hook not found: {hook_id}")


def delete(hook_id: str) -> None:
    with _LOCK:
        rows = _read(); kept = [row for row in rows if row.get("id") != hook_id]
        if len(kept) == len(rows): raise FileNotFoundError(f"Hook not found: {hook_id}")
        _write(kept)


def log(hook_id: str) -> list[dict[str, Any]]:
    try: rows = [json.loads(line) for line in _LOG.read_text(encoding="utf-8").splitlines() if line]
    except FileNotFoundError: return []
    return [row for row in rows if row.get("hook_id") == hook_id]


def fire(event: dict[str, Any]) -> None:
    for hook in _read():
        if hook.get("enabled") and hook.get("event") == event.get("type") and hook.get("agent_id") == event.get("agent_id"):
            threading.Thread(target=_run, args=(hook, event), daemon=True).start()


def _run(hook: dict[str, Any], event: dict[str, Any]) -> None:
    status = "succeeded"; message = ""
    try:
        action = hook["action"]
        if action["type"] == "webhook":
            request = urllib.request.Request(action["url"], data=json.dumps(event).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=10): pass
        elif action["type"] == "append_log_file":
            path = Path(action["path"]); path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        else:
            job = gitjobs.create_hook_job(list(action["command"]), event)
            launched = gitjobs.approve(str(job["id"]))
            message = f"job_id={launched['id']}; receipt={launched['approval_receipt']['binding_hash']}"
    except Exception as exc: status, message = "failed", str(exc)
    record = {"hook_id": hook["id"], "event": event.get("type"), "run_id": event.get("run_id"), "ts": runtime_state.now_iso(), "status": status, "message": message}
    with _LOCK:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as handle: handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        rows = _read()
        for row in rows:
            if row.get("id") == hook["id"]:
                row["executed_count"] = int(row.get("executed_count") or 0) + 1; row["last_run_at"] = record["ts"]; row["last_status"] = status
        _write(rows)
