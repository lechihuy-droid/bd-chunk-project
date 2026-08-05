from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import config
from services import audit, retention


@pytest.fixture()
def runtime_tmp(monkeypatch, tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    monkeypatch.setattr(config, "RUNTIME_DIR", base)
    monkeypatch.setattr(config, "RUNTIME_RUNS_DIR", base / "runs")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", base / "store")
    return base


def _old(path: Path, now: datetime) -> None:
    stamp = (now - timedelta(days=8)).timestamp()
    os.utime(path, (stamp, stamp))


def test_sweep_removes_only_old_operational_data(runtime_tmp: Path, monkeypatch, tmp_path: Path) -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    jobs = runtime_tmp / "jobs"; monkeypatch.setattr(config, "JOBS_DIR", jobs)
    cache = runtime_tmp / ".cache"; monkeypatch.setattr(config, "HUB_DIR", runtime_tmp); monkeypatch.setattr(config, "CHAT_USAGE_FILE", cache / "chat_usage.jsonl")
    old_run = runtime_tmp / "runs" / "run-old"; old_run.mkdir(parents=True); old_event = old_run / "events.jsonl"; old_event.write_text("{}\n"); _old(old_event, now)
    active_run = runtime_tmp / "runs" / "run-active"; active_run.mkdir(parents=True); active_event = active_run / "events.jsonl"; active_event.write_text("{}\n"); (active_run / "state.json").write_text(json.dumps({"status": "running"})); _old(active_event, now)
    artifact = old_run / "artifacts" / "keep.md"; artifact.parent.mkdir(); artifact.write_text("keep"); _old(artifact, now)
    old_job = jobs / "j-old"; old_job.mkdir(parents=True); job_log = old_job / "stdout.log"; job_log.write_text("old"); (old_job / "job.json").write_text(json.dumps({"status": "accepted"})); _old(job_log, now)
    evidence = audit.append("test.evidence"); audit_path = runtime_tmp / "store" / "security_audit.jsonl"; _old(audit_path, now)
    config.CHAT_USAGE_FILE.parent.mkdir(parents=True); config.CHAT_USAGE_FILE.write_text("cache\n"); _old(config.CHAT_USAGE_FILE, now)
    result = retention.sweep(now)
    assert result["removed_count"] == 3
    assert not old_event.exists() and not job_log.exists() and not config.CHAT_USAGE_FILE.exists()
    assert evidence["action"] == "test.evidence" and active_event.exists() and artifact.exists() and audit_path.exists()
