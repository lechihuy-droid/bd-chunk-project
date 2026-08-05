from __future__ import annotations

import json
from typing import Any

from services import audit, governance, risk, runtime_state, security


def _path():
    return runtime_state.runtime_path("store", "", "guardrail_decisions.jsonl")


def record_decision(decision: dict[str, Any]) -> dict[str, Any]:
    row = {
        "ts": runtime_state.now_iso(),
        "subject_id": str(decision.get("subject_id") or ""),
        "decision": str(decision.get("decision") or "allow"),
        "tier": str(decision.get("tier") or risk.UNKNOWN),
        "reasons": [str(item) for item in decision.get("reasons", [])] if isinstance(decision.get("reasons"), list) else [],
        "metadata": security.redact(decision.get("metadata")) if isinstance(decision.get("metadata"), dict) else {},
    }
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    if row["decision"] == "deny":
        governance.record_denial(row["subject_id"], row["reasons"] or ["guardrail denial"])
        audit.append("policy.denial", subject_id=row["subject_id"], policy_evaluation_id=str(decision.get("policy_evaluation_id") or ""), context=row)
    return row


def decide_command(subject_id: str, command: Any) -> dict[str, Any]:
    tier = risk.classify_command(command)
    blocked = set(governance.effective_blocked_tiers())
    denied = tier in blocked
    reasons = [f"tier blocked by governance: {tier}"] if denied else []
    return record_decision(
        {
            "subject_id": subject_id,
            "decision": "deny" if denied else "allow",
            "tier": tier,
            "reasons": reasons,
            "metadata": {"command": command},
        }
    )


def list_decisions(limit: int = 100) -> list[dict[str, Any]]:
    path = _path()
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
    return rows[-limit:]
