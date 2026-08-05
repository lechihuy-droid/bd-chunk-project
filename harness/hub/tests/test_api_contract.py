from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server
from services import boundary, gitjobs, workflow


@pytest.fixture()
def client() -> TestClient:
    server._IDEMPOTENCY_RESULTS.clear()
    return TestClient(server.app, headers={"x-hub-client": "harness-hub"})


def test_error_envelope_and_correlation_are_safe_and_uniform(client: TestClient) -> None:
    response = client.get("/api/workflows/..%5C..%5CWindows%5Csecret/source", headers={"X-Correlation-ID": "corr-contract"})

    assert response.status_code == 403
    assert response.headers["X-Correlation-ID"] == "corr-contract"
    assert response.headers["X-Schema-Version"] == "1"
    error = response.json()["error"]
    assert error == {"code": "FORBIDDEN", "message": "Access denied", "correlation_id": "corr-contract"}
    assert "Windows" not in response.text
    assert "C:\\" not in response.text


def test_sse_events_receive_request_correlation() -> None:
    async def source():
        yield 'event: done\ndata: {"ok": true}\n\n'

    async def collect() -> list[str]:
        return [chunk async for chunk in server._correlated_sse(source(), "corr-event")]

    data = json.loads(asyncio.run(collect())[0].split("data: ", 1)[1])
    assert data["correlation_id"] == "corr-event"
    assert data["schema_version"] == 1


def test_idempotency_key_replays_first_job_result(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def create_job(brief: str, agent: str, *, allow_override: bool = False) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"id": "job-contract", "brief": brief, "agent": agent}

    monkeypatch.setattr(gitjobs, "create_job", create_job)
    headers = {"Idempotency-Key": "job-create-contract"}
    first = client.post("/api/jobs", json={"brief": "create once", "agent": "codex"}, headers=headers)
    second = client.post("/api/jobs", json={"brief": "create once", "agent": "codex"}, headers=headers)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert second.headers["Idempotency-Replayed"] == "true"
    assert calls == 1


def test_stale_workflow_if_match_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    source = "id: demo\nnodes: []\nedges: []\nstop: {}\n"
    path = workflows_dir / "demo.workflow.yaml"
    path.write_text(source, encoding="utf-8")
    monkeypatch.setattr(workflow, "WORKFLOWS_DIR", workflows_dir)
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", tmp_path.resolve())

    current = client.get("/api/workflows/demo/source")
    path.write_text(source + "# changed\n", encoding="utf-8")
    stale = client.put("/api/workflows/demo", json={"yaml_text": source}, headers={"If-Match": current.headers["ETag"]})

    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_DOCUMENT"
    assert path.read_text(encoding="utf-8") == source + "# changed\n"
