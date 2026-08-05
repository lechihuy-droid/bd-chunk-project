from __future__ import annotations

import json
import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from services import audit, runtime_state


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
    return [row for row in _read_jsonl("memory.jsonl") if _usable(row)]


def _usable(row: dict[str, Any]) -> bool:
    if row.get("revoked_at"):
        return False
    value = (row.get("provenance") or {}).get("expires_at")
    if not isinstance(value, str):
        return False
    try:
        expires_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at.astimezone(UTC) > datetime.now(UTC)


def list_candidates() -> list[dict[str, Any]]:
    return _read_jsonl("memory_candidates.jsonl")


def create_candidate(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate = {
        "id": f"memory-candidate-{uuid.uuid4().hex[:10]}",
        "text": str(text),
        "status": "pending",
        "created_at": runtime_state.now_iso(),
        "metadata": dict(metadata or {}),
        "provenance": {"source": "runtime_candidate", "scope": "local", "classification": "internal"},
    }
    rows = list_candidates()
    rows.append(candidate)
    _write_jsonl("memory_candidates.jsonl", rows)
    return candidate


def _transition_candidate(candidate_id: str, status: str, acceptance: dict[str, Any] | None = None) -> dict[str, Any]:
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
            provenance = dict(updated.get("provenance") or {})
            provenance.update(acceptance or {})
            required = ("source", "accepted_by", "reason", "scope", "classification", "expires_at")
            missing = [key for key in required if not isinstance(provenance.get(key), str) or not provenance[key].strip()]
            if missing:
                raise ValueError(f"Memory acceptance provenance missing: {', '.join(missing)}")
            content = str(updated.get("text") or "")
            memory = list_memory()
            memory.append(
                {
                    "id": f"memory-{uuid.uuid4().hex[:10]}",
                    "candidate_id": candidate_id,
                    "text": content,
                    "created_at": updated["accepted_at"],
                    "metadata": updated.get("metadata") if isinstance(updated.get("metadata"), dict) else {},
                    "provenance": provenance,
                    "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "revoked_at": None,
                }
            )
            _write_jsonl("memory.jsonl", memory)
            audit.append("memory.accepted", subject_id=candidate_id, context={"content_hash": memory[-1]["content_hash"], "provenance": provenance})
        return updated
    raise FileNotFoundError(f"Memory candidate not found: {candidate_id}")


def accept_candidate(candidate_id: str, acceptance: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(acceptance, dict) or not str(acceptance.get("accepted_by") or "").strip() or not str(acceptance.get("reason") or "").strip():
        raise ValueError("Memory acceptance requires reviewer and rationale")
    return _transition_candidate(candidate_id, "accepted", acceptance)


def reject_candidate(candidate_id: str) -> dict[str, Any]:
    return _transition_candidate(candidate_id, "rejected")


def revoke_memory(memory_id: str, revoked_by: str, reason: str) -> dict[str, Any]:
    if not str(revoked_by).strip() or not str(reason).strip():
        raise ValueError("Memory revocation requires reviewer and reason")
    rows = list_memory()
    for index, row in enumerate(rows):
        if row.get("id") != memory_id:
            continue
        if row.get("revoked_at"):
            raise ValueError(f"Memory already revoked: {memory_id}")
        updated = dict(row)
        updated["revoked_at"] = runtime_state.now_iso()
        updated["revoked_by"] = str(revoked_by)
        updated["revocation_reason"] = str(reason)
        rows[index] = updated
        _write_jsonl("memory.jsonl", rows)
        audit.append("memory.revoked", subject_id=memory_id, context={"revoked_by": revoked_by, "reason": reason})
        return updated
    raise FileNotFoundError(f"Memory not found: {memory_id}")
