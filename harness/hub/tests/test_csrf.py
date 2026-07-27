from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import config
import server
from services import boundary, gitjobs


@pytest.fixture()
def raw_client() -> TestClient:
    return TestClient(server.app)


def test_get_allowed_without_header(raw_client: TestClient) -> None:
    assert raw_client.get("/api/health").status_code == 200


def test_post_blocked_without_client_header(raw_client: TestClient) -> None:
    resp = raw_client.post("/api/runs/trigger", json={"suite": "x"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "missing hub client header"


def test_post_blocked_cross_origin(raw_client: TestClient) -> None:
    resp = raw_client.post(
        "/api/runs/trigger",
        json={"suite": "x"},
        headers={"origin": "https://evil.example", "x-hub-client": "harness-hub"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "cross-origin blocked"


def test_post_passes_csrf_with_header(raw_client: TestClient) -> None:
    # Valid client header + local origin passes CSRF; handler then rejects unknown suite (not 403).
    resp = raw_client.post(
        "/api/runs/trigger",
        json={"suite": "does-not-exist"},
        headers={"origin": "http://127.0.0.1:8799", "x-hub-client": "harness-hub"},
    )
    assert resp.status_code != 403


def test_reconcile_orphans(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    job_dir = jobs_dir / "j-20260714-abcdef0123"
    job_dir.mkdir(parents=True)
    (job_dir / "job.json").write_text(
        json.dumps({"id": "j-20260714-abcdef0123", "status": "running"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", tmp_path.resolve())
    gitjobs._STREAMS.clear()

    orphaned = gitjobs.reconcile_orphans()

    assert orphaned == ["j-20260714-abcdef0123"]
    data = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["error"] == "orphaned by restart"
