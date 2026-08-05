from __future__ import annotations

import json
from pathlib import Path

import pytest

import config
from services import audit, runtime_events, runtime_memory, runtime_state, security


@pytest.fixture()
def runtime_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    monkeypatch.setattr(config, "RUNTIME_DIR", base)
    monkeypatch.setattr(config, "RUNTIME_THREADS_DIR", base / "threads")
    monkeypatch.setattr(config, "RUNTIME_RUNS_DIR", base / "runs")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", base / "store")
    return base


def test_audit_chain_rejects_rewrite(runtime_tmp: Path) -> None:
    audit.append("approval.used", subject_id="job-1", context={"target": "safe"})
    audit.append("policy.denial", subject_id="job-2", context={"reason": "blocked"})
    path = runtime_tmp / "store" / "security_audit.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    rows[0] = rows[0].replace("safe", "mutated")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    assert audit.verify() is False
    with pytest.raises(RuntimeError, match="integrity"):
        audit.append("settings.changed")


def test_secret_redaction_covers_event_log_and_error(runtime_tmp: Path) -> None:
    secret = "sk-abcdefghijklmnopqrstuvwxyz123456"
    run = runtime_state.create_run()
    runtime_events.append_event(run["run_id"], "error", message=f"provider token={secret}")
    event_body = (runtime_tmp / "runs" / run["run_id"] / "events.jsonl").read_text(encoding="utf-8")
    log = security.redact_text(f"stdout authorization=Bearer {secret}")
    error = security.redact_text(f"error api_key={secret}")
    assert secret not in event_body
    assert secret not in log
    assert secret not in error
    env = security.subprocess_env()
    assert "NVIDIA_API_KEY" not in env
    assert set(env).issubset({"APPDATA", "COMSPEC", "LOCALAPPDATA", "PATH", "PATHEXT", "PYTHONIOENCODING", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE"})


def test_memory_acceptance_rejects_missing_provenance(runtime_tmp: Path) -> None:
    path = runtime_tmp / "store" / "memory_candidates.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"id": "memory-candidate-bad", "text": "untrusted", "status": "pending"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="provenance missing"):
        runtime_memory.accept_candidate("memory-candidate-bad", {"accepted_by": "reviewer", "reason": "ok", "expires_at": "2030-01-01T00:00:00Z"})


def test_memory_acceptance_requires_real_reviewer_and_rationale(runtime_tmp: Path) -> None:
    candidate = runtime_memory.create_candidate("needs review")
    with pytest.raises(ValueError, match="reviewer and rationale"):
        runtime_memory.accept_candidate(candidate["id"])
    with pytest.raises(ValueError, match="reviewer and rationale"):
        runtime_memory.accept_candidate(candidate["id"], {"accepted_by": "reviewer"})


def test_memory_acceptance_has_immutable_hash_and_revocation(runtime_tmp: Path) -> None:
    candidate = runtime_memory.create_candidate("record provenance")
    runtime_memory.accept_candidate(candidate["id"], {"accepted_by": "reviewer", "reason": "useful", "expires_at": "2030-01-01T00:00:00Z"})
    memory = runtime_memory.list_memory()[0]
    assert memory["content_hash"]
    assert memory["provenance"]["scope"] == "local"
    assert runtime_memory.revoke_memory(memory["id"], "reviewer", "expired")["revoked_at"]


def test_revoked_or_expired_memory_is_not_listed(runtime_tmp: Path) -> None:
    expired = runtime_memory.create_candidate("expired")
    runtime_memory.accept_candidate(expired["id"], {"accepted_by": "reviewer", "reason": "test", "expires_at": "2000-01-01T00:00:00Z"})
    active = runtime_memory.create_candidate("active")
    runtime_memory.accept_candidate(active["id"], {"accepted_by": "reviewer", "reason": "test", "expires_at": "2030-01-01T00:00:00Z"})
    memory = runtime_memory.list_memory()[0]
    runtime_memory.revoke_memory(memory["id"], "reviewer", "test")
    assert runtime_memory.list_memory() == []
