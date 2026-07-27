from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import config
from services import risk


MAX_RECENT = 50


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_state() -> dict[str, Any]:
    return {
        "degradation": 0,
        "clean_streak": 0,
        "recent_denials": [],
        "recent_findings": [],
    }


def _load_state() -> dict[str, Any]:
    try:
        data = json.loads(config.GOVERNANCE_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_state()
    if not isinstance(data, dict):
        return _default_state()
    state = _default_state()
    state.update(data)
    try:
        state["degradation"] = max(0, min(4, int(state.get("degradation") or 0)))
    except (TypeError, ValueError):
        state["degradation"] = 0
    try:
        state["clean_streak"] = max(0, int(state.get("clean_streak") or 0))
    except (TypeError, ValueError):
        state["clean_streak"] = 0
    if not isinstance(state.get("recent_denials"), list):
        state["recent_denials"] = []
    if not isinstance(state.get("recent_findings"), list):
        state["recent_findings"] = []
    return state


def _save_state(state: dict[str, Any]) -> None:
    config.GOVERNANCE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.GOVERNANCE_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _base_blocked() -> set[str]:
    values = getattr(config, "JOB_BLOCKED_TIERS", ["destructive"])
    if not isinstance(values, list):
        return {"destructive"}
    return {str(item) for item in values if str(item) in risk.TIER_RANK}


def effective_blocked_tiers(level: int | None = None) -> list[str]:
    if level is None:
        level = int(_load_state().get("degradation") or 0)
    blocked = _base_blocked()
    if level >= 2:
        blocked.add("network")
    if level >= 3:
        blocked.add("execute")
    if level >= 4:
        blocked.update(tier for tier in risk.TIERS if tier != "read_only")
    return [tier for tier in risk.TIERS if tier in blocked]


def _trim(items: list[Any]) -> list[Any]:
    return items[:MAX_RECENT]


def record_findings(job_id: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    if not findings:
        return _load_state()
    state = _load_state()
    rows = [
        {
            "ts": _now(),
            "job_id": job_id,
            "pattern": str(item.get("pattern") or ""),
            "type": str(item.get("type") or ""),
            "offset": int(item.get("offset") or 0),
        }
        for item in findings
        if isinstance(item, dict)
    ]
    state["recent_findings"] = _trim([*reversed(rows), *state["recent_findings"]])
    _save_state(state)
    return state


def record_denial(job_id: str, reasons: list[str], escalate: bool = False) -> dict[str, Any]:
    state = _load_state()
    state["recent_denials"] = _trim(
        [
            {"ts": _now(), "job_id": job_id, "reasons": [str(reason) for reason in reasons]},
            *state["recent_denials"],
        ]
    )
    if escalate:
        state["degradation"] = min(4, int(state.get("degradation") or 0) + 1)
        state["clean_streak"] = 0
    _save_state(state)
    return state


def raise_degradation(job_id: str = "", reasons: list[str] | None = None) -> dict[str, Any]:
    if reasons:
        return record_denial(job_id, reasons, escalate=True)
    state = _load_state()
    state["degradation"] = min(4, int(state.get("degradation") or 0) + 1)
    state["clean_streak"] = 0
    _save_state(state)
    return state


def record_clean_job() -> dict[str, Any]:
    state = _load_state()
    if int(state.get("degradation") or 0) <= 0:
        state["clean_streak"] = 0
        _save_state(state)
        return state
    state["clean_streak"] = int(state.get("clean_streak") or 0) + 1
    if state["clean_streak"] >= int(config.GOV_RECOVERY_STEPS):
        state["degradation"] = max(0, int(state.get("degradation") or 0) - 1)
        state["clean_streak"] = 0
    _save_state(state)
    return state


def status() -> dict[str, Any]:
    state = _load_state()
    return {
        "degradation": int(state.get("degradation") or 0),
        "blocked_tiers": effective_blocked_tiers(int(state.get("degradation") or 0)),
        "recent_denials": list(state.get("recent_denials") or []),
        "recent_findings": list(state.get("recent_findings") or []),
    }
