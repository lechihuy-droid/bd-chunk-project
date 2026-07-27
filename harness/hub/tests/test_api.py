from __future__ import annotations

import io
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import config
import server
from services import behavior, boundary, gitjobs, runs, trigger, workflow


FIXTURE_RUNS_DIR = Path(__file__).resolve().parent / "fixtures" / "runs"
FIXTURE_BOARD_DIR = Path(__file__).resolve().parent / "fixtures" / "board"
FIXTURE_REPLAY_DIR = Path(__file__).resolve().parent / "fixtures" / "replay"
FIXTURE_USAGE_DIR = Path(__file__).resolve().parent / "fixtures" / "usage"
FIXTURE_RUN_ID = "20260627-234104-workspace-smoke"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setattr(config, "RUNS_DIR", FIXTURE_RUNS_DIR)
    monkeypatch.setattr(config, "JOBS_DIR", tmp_path / "api-jobs")
    monkeypatch.setattr(config, "GOVERNANCE_STATE_FILE", tmp_path / ".cache" / "governance.json")
    monkeypatch.setattr(config, "JOB_BLOCKED_TIERS", ["destructive"])
    monkeypatch.setattr(config, "OPUS_AI_DIR", FIXTURE_BOARD_DIR)
    monkeypatch.setattr(
        config,
        "USAGE_SOURCES",
        {
            "claude": FIXTURE_REPLAY_DIR / "claude_projects",
            "codex": [FIXTURE_REPLAY_DIR / "codex_sessions"],
            "inspect": FIXTURE_USAGE_DIR / "inspect_logs",
        },
    )
    runs._RUNS_CACHE.update({"expires": 0.0, "base": None, "items": []})
    monkeypatch.setattr(behavior, "_DISK_CACHE", tmp_path / "api-behavior.json")
    behavior._BEHAVIOR_CACHE.update(
        {"expires": 0.0, "events": [], "warnings": [], "sessions": [], "entropy": [], "fingerprint": None}
    )
    trigger._STREAMS.clear()
    gitjobs._STREAMS.clear()
    return TestClient(server.app, headers={"x-hub-client": "harness-hub"})


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["port"] == 8799


def test_workflow_source_reads_raw_file_and_rejects_traversal(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    source = "id: demo\nnodes: []\nedges: []\nstop: {}\n"
    (workflows_dir / "demo.workflow.yaml").write_text(source, encoding="utf-8")
    monkeypatch.setattr(workflow, "WORKFLOWS_DIR", workflows_dir)
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", tmp_path.resolve())

    response = client.get("/api/workflows/demo/source")
    assert response.status_code == 200
    assert response.json() == {"id": "demo", "yaml_text": source}
    assert client.get("/api/workflows/missing/source").status_code == 404
    traversal = "/api/workflows/..%5C..%5C..%5CWindows%5Cwin/source"
    assert client.get(traversal).status_code == 403


@pytest.fixture()
def sandboxed_workflows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """WORKFLOWS_DIR one level below the boundary root, so `..` escapes but stays readable."""
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    monkeypatch.setattr(workflow, "WORKFLOWS_DIR", workflows_dir)
    monkeypatch.setattr(boundary, "ROOT_RESOLVED", tmp_path.resolve())
    monkeypatch.setattr(
        workflow.runtime_agents,
        "list_agents",
        lambda: [{"id": "reviewer", "name": "Review Worker"}],
    )
    return tmp_path


def _outside_workflow(prompt: str) -> str:
    return yaml.safe_dump({
        "id": "..\\outside",
        "nodes": [
            {"id": "plan", "agent": "reviewer", "prompt": prompt, "gate": "none"},
            {"id": "act", "agent": "reviewer", "prompt": "Execute: {{plan_output}}", "gate": "none"},
        ],
        "edges": [["plan", "act"]],
        "stop": {"max_nodes": 10, "max_seconds": 1800},
    })


def test_workflow_validate_by_id_rejects_traversal(client: TestClient, sandboxed_workflows: Path) -> None:
    # Unguarded this reads the file above WORKFLOWS_DIR and answers 200 with its contents validated.
    (sandboxed_workflows / "outside.workflow.yaml").write_text(
        _outside_workflow("Plan: {{objective}}"), encoding="utf-8"
    )

    response = client.post("/api/workflows/validate", json={"id": "..\\outside"})

    assert response.status_code == 403


def test_workflow_run_rejects_traversal(client: TestClient, sandboxed_workflows: Path) -> None:
    # Unguarded this reads the file above WORKFLOWS_DIR and answers 400 for its malformed YAML.
    (sandboxed_workflows / "notes.workflow.yaml").write_text("not: [a workflow", encoding="utf-8")

    response = client.post("/api/workflows/..%5Cnotes/runs", json={"objective": "leak"})

    assert response.status_code == 403


def test_workflow_save_rejects_traversal(client: TestClient, sandboxed_workflows: Path) -> None:
    # Unguarded this backs up and overwrites the file above WORKFLOWS_DIR.
    outside = sandboxed_workflows / "outside.workflow.yaml"
    original = _outside_workflow("Plan: {{objective}}")
    outside.write_text(original, encoding="utf-8")

    response = client.put(
        "/api/workflows/..%5Coutside",
        json={"yaml_text": _outside_workflow("Overwritten: {{objective}}")},
    )

    assert response.status_code == 403
    assert outside.read_text(encoding="utf-8") == original
    assert list(sandboxed_workflows.glob("outside.workflow.yaml.bak-*")) == []


def test_runs_endpoints(client: TestClient) -> None:
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert response.json()[0]["run_id"] == FIXTURE_RUN_ID

    detail = client.get(f"/api/runs/{FIXTURE_RUN_ID}")
    assert detail.status_code == 200
    assert detail.json()["summary"]["total"] == 11

    missing = client.get("/api/runs/missing")
    assert missing.status_code == 404


def test_artifact_endpoint_boundary(client: TestClient) -> None:
    response = client.get(f"/api/runs/{FIXTURE_RUN_ID}/artifact", params={"rel": "report.md"})
    assert response.status_code == 200
    assert "Harness Report" in response.text

    outside = client.get(f"/api/runs/{FIXTURE_RUN_ID}/artifact", params={"rel": "../outside.txt"})
    assert outside.status_code == 403


def test_suites_endpoints(client: TestClient) -> None:
    response = client.get("/api/suites")
    assert response.status_code == 200
    assert any(item["id"] == "workspace-smoke" for item in response.json())

    detail = client.get("/api/suites/workspace-smoke")
    assert detail.status_code == 200
    assert detail.json()["check_count"] >= 11


def test_trigger_rejects_unknown_suite(client: TestClient) -> None:
    response = client.post("/api/runs/trigger", json={"suite": "missing-suite"})
    assert response.status_code == 400


def test_jobs_reject_unknown_agent(client: TestClient) -> None:
    response = client.post("/api/jobs", json={"brief": "test", "agent": "unknown"})
    assert response.status_code == 400


def test_jobs_bad_id_returns_404(client: TestClient) -> None:
    response = client.get("/api/jobs/not-a-valid-job-id!")
    assert response.status_code == 404


def test_trigger_streams_mocked_subprocess(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    class FakeProcess:
        stdout = io.StringIO('hello\n{"run_id":"fake-run"}\n')
        stderr = io.StringIO("warn\n")

        def wait(self) -> int:
            return 0

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        calls.append((command, kwargs))
        return FakeProcess()

    monkeypatch.setattr(trigger.subprocess, "Popen", fake_popen)

    started = client.post("/api/runs/trigger", json={"suite": "workspace-smoke"})
    assert started.status_code == 200
    stream_id = started.json()["stream_id"]
    assert stream_id

    streamed = client.get(f"/api/runs/stream/{stream_id}")
    assert streamed.status_code == 200
    assert "event: line" in streamed.text
    assert "hello" in streamed.text
    assert "fake-run" in streamed.text
    assert "event: exit" in streamed.text

    command, kwargs = calls[0]
    assert command[1].endswith("harness\\run_harness.py") or command[1].endswith("harness/run_harness.py")
    assert command[2:] == ["--suite", "workspace-smoke", "--json"]
    assert kwargs["cwd"] == config.ROOT
    assert kwargs["shell"] is False


def test_phase3_read_endpoints(client: TestClient) -> None:
    board_response = client.get("/api/board")
    assert board_response.status_code == 200
    assert board_response.json()["owner"] == "codex"

    sessions_response = client.get("/api/sessions")
    assert sessions_response.status_code == 200
    assert {item["source"] for item in sessions_response.json()} == {"claude", "codex"}

    inspect_response = client.get("/api/inspect/logs")
    assert inspect_response.status_code == 200
    assert isinstance(inspect_response.json(), list)


def test_behavior_endpoints(client: TestClient) -> None:
    tools_response = client.get("/api/tools")
    assert tools_response.status_code == 200
    tools = tools_response.json()
    assert tools["totals"]["tool_calls"] == 4
    assert any(row["tool"] == "Bash" and row["count"] == 1 for row in tools["by_tool"])
    assert any(row["tool"] == "functions.shell_command" and row["count"] == 1 for row in tools["by_tool"])

    filtered = client.get("/api/tools", params={"source": "codex", "model": "gpt-5-codex"})
    assert filtered.status_code == 200
    assert filtered.json()["totals"]["tool_calls"] == 2

    loops_response = client.get("/api/sessions/loops")
    assert loops_response.status_code == 200
    loops = loops_response.json()
    assert len(loops) == 2
    assert all("loop_risk" in item for item in loops)


def test_group_a_read_endpoints(client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    entropy_response = client.get("/api/sessions/entropy")
    assert entropy_response.status_code == 200
    entropy = entropy_response.json()
    assert len(entropy) == 2
    assert all("max_violation_rate" in item for item in entropy)

    suites_dir = tmp_path / "suites"
    suites_dir.mkdir()
    (suites_dir / "api-suite.json").write_text('{"id":"api-suite","checks":[]}\n', encoding="utf-8")
    monkeypatch.setattr(config, "SUITES_DIR", suites_dir)
    monkeypatch.setattr(config, "HMAC_KEY_FILE", tmp_path / ".hmac_key")
    monkeypatch.setattr(config, "INTEGRITY_SIGS_FILE", tmp_path / ".cache" / "suite_sigs.json")

    integrity_response = client.get("/api/integrity")
    assert integrity_response.status_code == 200
    integrity = integrity_response.json()
    assert integrity["ok"] is True
    assert integrity["count"] == 1
    assert integrity["suites"][0]["suite"] == "api-suite.json"


def test_governance_endpoint(client: TestClient) -> None:
    response = client.get("/api/governance")

    assert response.status_code == 200
    data = response.json()
    assert data["degradation"] == 0
    assert data["blocked_tiers"] == ["destructive"]
    assert data["recent_denials"] == []
    assert data["recent_findings"] == []


def test_spa_index(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Harness Hub" in response.text
