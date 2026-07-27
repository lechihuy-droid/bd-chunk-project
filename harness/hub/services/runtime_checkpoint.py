from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services import runtime_state


def _checkpoint_dir(thread_id: str) -> Path:
    path = runtime_state.runtime_path("thread", thread_id, "checkpoints")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _checkpoint_path(thread_id: str, checkpoint_id: str) -> Path:
    runtime_state.validate_id("checkpoint", checkpoint_id)
    return runtime_state.runtime_path("thread", thread_id, "checkpoints", f"{checkpoint_id}.json")


def write_checkpoint(
    run_id: str,
    *,
    state: dict[str, Any] | None = None,
    checkpoint_id: str | None = None,
    reason: str = "",
) -> dict[str, Any]:
    snapshot_state = state or runtime_state.read_run(run_id)
    run_id = runtime_state.validate_id("run", str(snapshot_state.get("run_id") or run_id))
    thread_id = runtime_state.validate_id("thread", str(snapshot_state.get("thread_id") or ""))
    checkpoint = {
        "checkpoint_id": checkpoint_id or runtime_state.new_id("checkpoint"),
        "run_id": run_id,
        "thread_id": thread_id,
        "created_at": runtime_state.now_iso(),
        "reason": reason,
        "state": snapshot_state,
    }
    path = _checkpoint_path(thread_id, str(checkpoint["checkpoint_id"]))
    path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    latest = runtime_state.runtime_path("thread", thread_id, "latest.json")
    latest.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    runtime_state.write_run_state(snapshot_state)
    return checkpoint


def read_checkpoint(thread_id: str, checkpoint_id: str) -> dict[str, Any]:
    path = _checkpoint_path(thread_id, checkpoint_id)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid checkpoint: {checkpoint_id}")
    return data


def read_latest(thread_id: str) -> dict[str, Any]:
    runtime_state.validate_id("thread", thread_id)
    path = runtime_state.runtime_path("thread", thread_id, "latest.json")
    if not path.is_file():
        raise FileNotFoundError(f"Latest checkpoint not found: {thread_id}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid latest checkpoint: {thread_id}")
    return data


def list_checkpoints(thread_id: str) -> list[dict[str, Any]]:
    runtime_state.validate_id("thread", thread_id)
    path = _checkpoint_dir(thread_id)
    items: list[dict[str, Any]] = []
    for checkpoint_path in path.glob("checkpoint-*.json"):
        try:
            with checkpoint_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                items.append(data)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return items
