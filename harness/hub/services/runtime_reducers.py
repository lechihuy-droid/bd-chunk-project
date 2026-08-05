from __future__ import annotations

from copy import deepcopy
from typing import Any


RUNTIME_STATUSES = {"queued", "running", "interrupted", "succeeded", "failed", "cancelled"}
STATE_LIST_FIELDS = ("messages", "artifacts", "tool_calls", "child_runs", "interrupts")
STATE_DICT_FIELDS = ("usage", "metadata")


def default_state(run_id: str = "", thread_id: str = "", status: str = "queued") -> dict[str, Any]:
    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "status": status,
        "messages": [],
        "artifacts": [],
        "tool_calls": [],
        "child_runs": [],
        "interrupts": [],
        "usage": {},
        "metadata": {},
    }


def normalize_state(value: dict[str, Any]) -> dict[str, Any]:
    state = default_state(
        run_id=str(value.get("run_id") or ""),
        thread_id=str(value.get("thread_id") or ""),
        status=str(value.get("status") or "queued"),
    )
    for field in STATE_LIST_FIELDS:
        raw = value.get(field)
        state[field] = list(raw) if isinstance(raw, list) else []
    for field in STATE_DICT_FIELDS:
        raw = value.get(field)
        state[field] = dict(raw) if isinstance(raw, dict) else {}
    if isinstance(value.get("state_version"), int):
        state["state_version"] = value["state_version"]
    if isinstance(value.get("runtime_compatibility"), str):
        state["runtime_compatibility"] = value["runtime_compatibility"]
    return state


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def _item_keys(item: Any, keys: tuple[str, ...]) -> list[str]:
    if not isinstance(item, dict):
        return []
    found: list[str] = []
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value:
            found.append(f"{key}:{value}")
    return found


def _merge_by_key(existing: list[Any], incoming: list[Any], keys: tuple[str, ...]) -> list[Any]:
    merged = deepcopy(existing)
    index: dict[str, int] = {}
    for position, item in enumerate(merged):
        for key in _item_keys(item, keys):
            index[key] = position

    for item in incoming:
        copied = deepcopy(item)
        item_keys = _item_keys(copied, keys)
        position = next((index[key] for key in item_keys if key in index), None)
        if position is not None:
            merged[position] = copied
            for key in item_keys:
                index[key] = position
        else:
            for key in item_keys:
                index[key] = len(merged)
            merged.append(copied)
    return merged


def _merge_usage(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(current)
    for key, value in update.items():
        if isinstance(value, int | float) and isinstance(merged.get(key), int | float):
            merged[key] = merged[key] + value
        elif isinstance(value, int | float) and key not in merged:
            merged[key] = value
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_usage(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def merge_state(state: dict[str, Any], update: dict[str, Any] | None) -> dict[str, Any]:
    if not update:
        return normalize_state(state)

    merged = normalize_state(state)
    for key, value in update.items():
        if key == "messages":
            merged[key] = _merge_by_key(merged[key], _as_list(value), ("id",))
        elif key == "artifacts":
            merged[key] = _merge_by_key(merged[key], _as_list(value), ("id", "path"))
        elif key == "tool_calls":
            merged[key] = [*deepcopy(merged[key]), *deepcopy(_as_list(value))]
        elif key == "child_runs":
            merged[key] = _merge_by_key(merged[key], _as_list(value), ("run_id",))
        elif key == "interrupts":
            merged[key] = _merge_by_key(merged[key], _as_list(value), ("interrupt_id",))
        elif key == "usage":
            merged[key] = _merge_usage(merged[key], value if isinstance(value, dict) else {})
        elif key == "metadata":
            patch = value if isinstance(value, dict) else {}
            merged[key] = {**deepcopy(merged[key]), **deepcopy(patch)}
        elif key == "status":
            merged[key] = str(value)
        elif key in {"run_id", "thread_id"}:
            merged[key] = str(value)
        else:
            merged[key] = deepcopy(value)
    return merged
