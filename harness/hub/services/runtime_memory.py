from __future__ import annotations

import json
import uuid
from typing import Any

from services import runtime_state


def _jsonl_path(name: str):
    return runtime_state.runtime_path("store", "", name)


def _read_jsonl(name: str) -> list[dict[str, Any]]:
    path = _jsonl_path(name)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    path = _jsonl_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def list_memory() -> list[dict[str, Any]]:
    return _read_jsonl("memory.jsonl")


def list_candidates() -> list[dict[str, Any]]:
    return _read_jsonl("memory_candidates.jsonl")


def create_candidate(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate = {
        "id": f"memory-candidate-{uuid.uuid4().hex[:10]}",
        "text": str(text),
        "status": "pending",
        "created_at": runtime_state.now_iso(),
        "metadata": dict(metadata or {}),
    }
    rows = list_candidates()
    rows.append(candidate)
    _write_jsonl("memory_candidates.jsonl", rows)
    return candidate


def _transition_candidate(candidate_id: str, status: str) -> dict[str, Any]:
    rows = list_candidates()
    for index, row in enumerate(rows):
        if row.get("id") != candidate_id:
            continue
        if row.get("status", "pending") != "pending":
            raise ValueError(f"Memory candidate is not pending: {candidate_id}")
        updated = dict(row)
        updated["status"] = status
        updated[f"{status}_at"] = runtime_state.now_iso()
        rows[index] = updated
        _write_jsonl("memory_candidates.jsonl", rows)
        if status == "accepted":
            memory = list_memory()
            memory.append(
                {
                    "id": f"memory-{uuid.uuid4().hex[:10]}",
                    "candidate_id": candidate_id,
                    "text": str(updated.get("text") or ""),
                    "created_at": updated["accepted_at"],
                    "metadata": updated.get("metadata") if isinstance(updated.get("metadata"), dict) else {},
                }
            )
            _write_jsonl("memory.jsonl", memory)
        return updated
    raise FileNotFoundError(f"Memory candidate not found: {candidate_id}")


def accept_candidate(candidate_id: str) -> dict[str, Any]:
    return _transition_candidate(candidate_id, "accepted")


def reject_candidate(candidate_id: str) -> dict[str, Any]:
    return _transition_candidate(candidate_id, "rejected")
