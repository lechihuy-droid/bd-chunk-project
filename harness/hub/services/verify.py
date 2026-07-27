from __future__ import annotations

from typing import Any

from services import inform, risk


DESTRUCTIVE_TOKEN_REASON = "destructive token without allow_override"
INJECTION_REASON = "L1 injection pattern"


def _lines_from_diff(diff_text: str) -> list[str]:
    lines: list[str] = []
    for line in str(diff_text or "").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:].strip())
    return lines


def _command_tiers(job: dict[str, Any]) -> list[str]:
    tiers: list[str] = []
    command = job.get("command")
    if command:
        tiers.append(risk.classify_command(command))
    diff_text = str(job.get("diff") or job.get("diff_text") or "")
    for line in _lines_from_diff(diff_text):
        tiers.append(risk.classify_command(line))
    return [tier for tier in tiers if tier != risk.UNKNOWN]


def rule_check(job: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    allow_override = bool(job.get("allow_override"))
    findings = job.get("inform_findings")

    if inform.has_injection_finding(findings):
        reasons.append(INJECTION_REASON)

    tiers = [str(job.get("max_tier") or "read_only"), *_command_tiers(job)]
    if not allow_override and any(tier == "destructive" for tier in tiers):
        reasons.append(DESTRUCTIVE_TOKEN_REASON)

    if reasons:
        return {"decision": "deny", "reasons": reasons}

    warn_tiers = [tier for tier in tiers if tier in {"network", "execute"}]
    if warn_tiers:
        unique = sorted(set(warn_tiers), key=lambda item: risk.TIER_RANK[item])
        return {"decision": "warn", "reasons": [f"tier warning: {', '.join(unique)}"]}

    return {"decision": "allow", "reasons": []}
