from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

import config
import server
from services import runtime_artifacts, runtime_state, workflow_exec
from services.providers import registry


@pytest.fixture()
def runtime_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    monkeypatch.setattr(config, "RUNTIME_DIR", base)
    monkeypatch.setattr(config, "RUNTIME_THREADS_DIR", base / "threads")
    monkeypatch.setattr(config, "RUNTIME_RUNS_DIR", base / "runs")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", base / "store")
    return base


class FakeProvider:
    def __init__(self, text: str) -> None:
        self.text = text

    def stream_chat(self, messages: list[dict[str, str]], session_id: str | None = None, model: str | None = None, **_: Any) -> Iterator[dict[str, Any]]:
        yield {"type": "delta", "text": self.text}
        yield {"type": "done", "usage": {}}


def _agent() -> dict[str, Any]:
    return {
        "id": "reviewer", "provider": "fake", "model": None, "system_prompt": "Review.",
        "budget": {"seconds": 60, "max_calls": 5}, "skills": [], "permission": "read_only", "risk_tier": "read_only",
    }


def _run() -> str:
    return str(runtime_state.create_run(agent_id="lead", metadata={"objective": "ship"})["run_id"])


def _fake_run(monkeypatch: pytest.MonkeyPatch, text: str = "full node output") -> str:
    monkeypatch.setitem(registry, "fake", FakeProvider(text))
    run_id = _run()
    ir = [{"id": "node-1", "agent": _agent(), "prompt": "Do {{objective}}", "gate": "none", "order": 0}]
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))
    return run_id


def test_write_and_list_node_artifact(runtime_tmp: Path) -> None:
    run_id = _run()
    rel = runtime_artifacts.write_node_artifact(run_id, "node-1", "full node output")
    assert rel == "artifacts/node-1.md"
    assert (runtime_state.run_dir(run_id) / rel).read_text(encoding="utf-8") == "full node output"
    assert runtime_artifacts.list_artifacts(run_id) == [{"name": "node-1.md", "chars": 16}]


def test_fake_run_emits_artifact_written_event(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = _fake_run(monkeypatch)
    events = [json.loads(line) for line in (runtime_state.run_dir(run_id) / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(event["type"] == "artifact_written" and event["node"] == "node-1" for event in events)


def test_artifact_api_lists_and_reads_node_artifact(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = _fake_run(monkeypatch, "api node output")
    client = TestClient(server.app)
    listed = client.get(f"/api/workflows/runs/{run_id}/artifacts")
    assert listed.status_code == 200
    assert listed.json()["artifacts"] == [{"name": "node-1.md", "chars": 15}]
    read = client.get(f"/api/workflows/runs/{run_id}/artifacts/node-1.md")
    assert read.status_code == 200
    assert read.json() == {"name": "node-1.md", "text": "api node output"}


def test_artifact_api_rejects_traversal(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = _fake_run(monkeypatch)
    client = TestClient(server.app)
    for path in (f"/api/workflows/runs/{run_id}/artifacts/..%2f..%2frun.json", f"/api/workflows/runs/{run_id}/artifacts/../run.json"):
        response = client.get(path)
        assert response.status_code == 404
        assert "run_id" not in response.text


def test_artifact_api_rejects_bad_run_id(runtime_tmp: Path) -> None:
    response = TestClient(server.app).get("/api/workflows/runs/not-a-run/artifacts")
    assert response.status_code == 404


def test_library_artifact_api_creates_reads_and_versions(runtime_tmp: Path) -> None:
    client = TestClient(server.app)
    headers = {config.HUB_CLIENT_HEADER: config.HUB_CLIENT_VALUE}
    created = client.post("/api/artifacts", headers=headers, json={"title": "Ghi chú", "content": "bản đầu", "source": "chat"})
    assert created.status_code == 200
    artifact = created.json()
    assert artifact["title"] == "Ghi chú"
    assert artifact["source"] == "chat"
    assert artifact["versions"] == [{"version": "v1", "created_at": artifact["created_at"], "content": "bản đầu"}]
    updated = client.post("/api/artifacts", headers=headers, json={"id": artifact["id"], "content": "bản hai", "source": "chat"})
    assert updated.status_code == 200
    assert [version["version"] for version in updated.json()["versions"]] == ["v1", "v2"]
    listed = client.get("/api/artifacts")
    assert listed.status_code == 200
    assert listed.json()["artifacts"][0]["versions"][-1] == {"version": "v2", "created_at": updated.json()["versions"][-1]["created_at"]}
    read = client.get(f"/api/artifacts/{artifact['id']}")
    assert read.status_code == 200
    assert read.json()["versions"][-1]["content"] == "bản hai"


def test_library_artifact_api_rejects_unknown_traversal_and_oversized(runtime_tmp: Path) -> None:
    client = TestClient(server.app)
    headers = {config.HUB_CLIENT_HEADER: config.HUB_CLIENT_VALUE}
    assert client.get("/api/artifacts/not-found").status_code == 404
    assert client.get("/api/artifacts/..%2Fartifacts.json").status_code == 404
    oversized = client.post("/api/artifacts", headers=headers, json={"title": "Too large", "content": "x" * (runtime_artifacts.MAX_ARTIFACT_CONTENT_CHARS + 1), "source": "chat"})
    assert oversized.status_code == 400
