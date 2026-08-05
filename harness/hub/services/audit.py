from __future__ import annotations

import hashlib
import json
import threading
import uuid
from typing import Any

from services import runtime_state, security


_LOCK = threading.Lock()
_GENESIS = "0" * 64


def _path():
    return runtime_state.runtime_path("store", "", "security_audit.jsonl")


def _digest(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "hash"}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def verify() -> bool:
    path = _path()
    previous = _GENESIS
    if not path.is_file():
        return True
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                return False
            if not isinstance(row, dict) or row.get("previous_hash") != previous or row.get("hash") != _digest(row):
                return False
            previous = str(row["hash"])
    return True


def append(action: str, *, subject_id: str = "", policy_evaluation_id: str = "", context: dict[str, Any] | None = None) -> dict[str, Any]:
    path = _path()
    with _LOCK:
        if not verify():
            raise RuntimeError("security audit evidence integrity check failed")
        previous = _GENESIS
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line:
                    previous = str(json.loads(line)["hash"])
        row = {
            "audit_id": f"audit-{uuid.uuid4().hex}",
            "ts": runtime_state.now_iso(),
            "action": str(action),
            "subject_id": str(subject_id),
            "policy_evaluation_id": str(policy_evaluation_id),
            "context": security.redact(context or {}),
            "previous_hash": previous,
        }
        row["hash"] = _digest(row)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row
