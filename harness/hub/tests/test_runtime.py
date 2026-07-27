from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import config
import server
from services import (
    runtime_checkpoint,
    runtime_children,
    runtime_events,
    runtime_interrupts,
    runtime_memory,
    runtime_reducers,
    runtime_skills,
    runtime_state,
)


@pytest.fixture()
def runtime_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    monkeypatch.setattr(config, "RUNTIME_DIR", base)
    monkeypatch.setattr(config, "RUNTIME_THREADS_DIR", base / "threads")
    monkeypatch.setattr(config, "RUNTIME_RUNS_DIR", base / "runs")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", base / "store")
    monkeypatch.setattr(config, "RUNTIME_MAX_CHILD_RUNS", 3)
    monkeypatch.setattr(config, "RUNTIME_CHILD_TIMEOUT_SECONDS", 900)
    monkeypatch.setattr(config, "GOVERNANCE_STATE_FILE", tmp_path / ".cache" / "governance.json")
    return base


def _sse_payloads(text: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for block in text.split("\n\n"):
        lines = [line for line in block.splitlines() if line.startswith("data:")]
        if not lines:
            continue
        payloads.append(json.loads("\n".join(line[5:].lstrip() for line in lines)))
    return payloads


def test_runtime_reducers_merge_state_fields() -> None:
    state = runtime_reducers.default_state("run-a", "thread-a")
    first = runtime_reducers.merge_state(
        state,
        {
            "messages": [{"id": "m1", "content": "old"}],
            "artifacts": [{"id": "a1", "path": "a.txt"}],
            "tool_calls": [{"id": "t1"}],
            "child_runs": [{"run_id": "run-child", "status": "queued"}],
            "interrupts": [{"interrupt_id": "interrupt-1", "status": "pending"}],
            "usage": {"tokens": 3, "nested": {"steps": 1}},
            "metadata": {"a": 1},
        },
    )
    merged = runtime_reducers.merge_state(
        first,
        {
            "messages": [{"id": "m1", "content": "new"}, {"id": "m2", "content": "two"}],
            "artifacts": [{"path": "a.txt", "title": "A"}, {"id": "a2", "path": "b.txt"}],
            "tool_calls": [{"id": "t2"}],
            "child_runs": [{"run_id": "run-child", "status": "succeeded"}],
            "interrupts": [{"interrupt_id": "interrupt-1", "status": "resolved"}],
            "usage": {"tokens": 4, "nested": {"steps": 2}},
            "metadata": {"b": 2},
        },
    )

    assert [item["content"] for item in merged["messages"]] == ["new", "two"]
    assert len(merged["artifacts"]) == 2
    assert merged["artifacts"][0]["title"] == "A"
    assert [item["id"] for item in merged["tool_calls"]] == ["t1", "t2"]
    assert merged["child_runs"][0]["status"] == "succeeded"
    assert merged["interrupts"][0]["status"] == "resolved"
    assert merged["usage"] == {"tokens": 7, "nested": {"steps": 3}}
    assert merged["metadata"] == {"a": 1, "b": 2}


def test_runtime_state_checkpoint_events_interrupts_and_boundaries(runtime_tmp: Path) -> None:
    run = runtime_state.create_run(messages=[{"id": "u1", "role": "user", "content": "hello"}])
    run_id = run["run_id"]
    thread_id = run["thread_id"]

    assert runtime_state.read_run(run_id)["messages"][0]["content"] == "hello"
    assert runtime_state.list_runs()[0]["run_id"] == run_id
    assert runtime_state.read_thread(thread_id)["latest_run_id"] == run_id

    runtime_events.append_event(run_id, "debug", message="one")
    runtime_events.append_event(run_id, "debug", message="two")
    assert [event["message"] for event in runtime_events.read_events(run_id)] == ["one", "two"]

    checkpoint = runtime_checkpoint.write_checkpoint(run_id, reason="test")
    assert runtime_checkpoint.read_latest(thread_id)["checkpoint_id"] == checkpoint["checkpoint_id"]
    assert runtime_checkpoint.list_checkpoints(thread_id)[0]["run_id"] == run_id

    interrupt = runtime_interrupts.create_interrupt(run_id, reason="approval_required", payload={"x": 1}, node="act")
    assert runtime_state.read_run(run_id)["status"] == "interrupted"
    resolved = runtime_interrupts.resolve_interrupt(run_id, interrupt["interrupt_id"], resume_payload={"approved": True})
    assert resolved["interrupt"]["status"] == "resolved"
    assert runtime_state.read_run(run_id)["status"] == "running"

    with pytest.raises(PermissionError):
        runtime_state.runtime_path("run", run_id, "..", "outside.json")
    with pytest.raises(FileNotFoundError):
        runtime_state.read_run("../outside")


def test_runtime_pipeline_api_create_interrupt_resume_and_404(runtime_tmp: Path) -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    response = client.post("/api/agent/runs", json={"objective": "api runtime smoke"})
    assert response.status_code == 200
    assert "event: node_update" in response.text
    assert "event: state_snapshot" in response.text
    assert "event: done" in response.text
    payloads = _sse_payloads(response.text)
    run_id = str(payloads[0]["run_id"])

    runs = client.get("/api/agent/runs")
    assert runs.status_code == 200
    assert runs.json()[0]["run_id"] == run_id

    detail = client.get(f"/api/agent/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "succeeded"

    events = client.get(f"/api/agent/runs/{run_id}/events")
    assert events.status_code == 200
    assert any(event["type"] == "done" for event in events.json())

    missing = client.get("/api/agent/runs/run-00000000-missing")
    assert missing.status_code == 404

    interrupted = client.post("/api/agent/runs", json={"objective": "needs approval", "require_approval": True})
    assert interrupted.status_code == 200
    assert "event: interrupt" in interrupted.text
    interrupted_run_id = str(_sse_payloads(interrupted.text)[0]["run_id"])
    interrupted_detail = client.get(f"/api/agent/runs/{interrupted_run_id}").json()
    pending = [item for item in interrupted_detail["interrupts"] if item["status"] == "pending"]
    assert pending

    resumed = client.post(
        f"/api/agent/runs/{interrupted_run_id}/interrupts/{pending[0]['interrupt_id']}/resume",
        json={"payload": {"approved": True}},
    )
    assert resumed.status_code == 200
    assert "event: done" in resumed.text
    assert client.get(f"/api/agent/runs/{interrupted_run_id}").json()["status"] == "succeeded"


def test_runtime_child_run_constraints_and_artifact_merge(runtime_tmp: Path) -> None:
    parent = runtime_state.create_run(
        metadata={"agent_id": "lead", "allowed_paths": ["harness/hub"], "allowed_tools": ["read"]},
    )
    parent_id = parent["run_id"]
    first = runtime_children.create_child_run(
        parent_id,
        {
            "objective": "inspect runtime",
            "allowed_paths": ["harness/hub"],
            "allowed_tools": ["read"],
            "agent_id": "reviewer",
        },
    )
    child_id = first["child_run"]["run_id"]
    assert runtime_state.read_run(parent_id)["child_runs"][0]["run_id"] == child_id

    with pytest.raises(ValueError):
        runtime_children.create_child_run(
            parent_id,
            {"objective": "expand", "allowed_paths": ["outside"], "allowed_tools": ["read"]},
        )

    runtime_children.create_child_run(parent_id, {"objective": "second", "allowed_paths": ["harness/hub"], "allowed_tools": ["read"]})
    runtime_children.create_child_run(parent_id, {"objective": "third", "allowed_paths": ["harness/hub"], "allowed_tools": ["read"]})
    with pytest.raises(ValueError):
        runtime_children.create_child_run(parent_id, {"objective": "fourth", "allowed_paths": ["harness/hub"], "allowed_tools": ["read"]})

    runtime_children.complete_child_run(child_id, [{"id": "child-artifact", "path": "artifacts/result.json"}])
    parent_after = runtime_state.read_run(parent_id)
    assert any(item.get("source_run_id") == child_id for item in parent_after["artifacts"])

    failed_child = runtime_state.read_run(parent_after["child_runs"][1]["run_id"])
    runtime_children.fail_child_run(failed_child["run_id"], "timeout", timed_out=True)
    assert runtime_state.read_run(failed_child["run_id"])["metadata"]["timed_out"] is True


def test_runtime_skills_memory_and_guardrail_apis(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Demo Skill\n\nUse for runtime tests.\n", encoding="utf-8")
    monkeypatch.setattr(runtime_skills, "_skill_roots", lambda: [tmp_path / "skills"])

    candidate = runtime_memory.create_candidate("Remember explicit approvals only")
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})

    skills = client.get("/api/skills")
    assert skills.status_code == 200
    skill_id = skills.json()[0]["id"]
    assert client.get(f"/api/skills/{skill_id}").json()["title"] == "Demo Skill"
    assert client.get(f"/api/skills/{skill_id}/usage").json()["count"] == 0

    candidates = client.get("/api/memory/candidates")
    assert candidates.status_code == 200
    assert candidates.json()[0]["id"] == candidate["id"]
    accepted = client.post(f"/api/memory/candidates/{candidate['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert client.get("/api/memory").json()[0]["candidate_id"] == candidate["id"]

    denied = client.post("/api/guardrails/decisions/command", json={"subject_id": "run-test", "command": "rm -rf ."})
    assert denied.status_code == 200
    assert denied.json()["decision"] in {"allow", "deny"}
    assert client.get("/api/guardrails/decisions").json()
