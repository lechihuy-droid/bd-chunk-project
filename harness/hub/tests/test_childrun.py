from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest

import config
from services import governance, runtime_interrupts, runtime_state, workflow_exec
from services.providers import registry


@pytest.fixture()
def runtime_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    base = tmp_path / "runtime"
    monkeypatch.setattr(config, "RUNTIME_DIR", base)
    monkeypatch.setattr(config, "RUNTIME_THREADS_DIR", base / "threads")
    monkeypatch.setattr(config, "RUNTIME_RUNS_DIR", base / "runs")
    monkeypatch.setattr(config, "RUNTIME_STORE_DIR", base / "store")
    monkeypatch.setattr(config, "GOVERNANCE_STATE_FILE", tmp_path / "governance.json")
    return base


class FakeProvider:
    def __init__(self, scripts: list[list[dict[str, Any]]]) -> None:
        self.scripts = scripts
        self.messages: list[list[dict[str, str]]] = []

    def stream_chat(self, messages: list[dict[str, str]], **_: Any) -> Iterator[dict[str, Any]]:
        self.messages.append(messages)
        yield from self.scripts.pop(0)


def _agent(agent_id: str, *, tier: str = "read_only") -> dict[str, Any]:
    return {"id": agent_id, "provider": "fake", "model": None, "system_prompt": "Do work.", "budget": {"seconds": 60, "max_calls": 5}, "skills": [], "permission": "read_only", "risk_tier": tier}


def _run() -> str:
    return str(runtime_state.create_run(agent_id="lead", metadata={"objective": "ship"})["run_id"])


def _ir(*, tier: str = "read_only") -> list[dict[str, Any]]:
    return [{"id": "parent", "agent": _agent("lead"), "prompt": "Do {{objective}}", "gate": "none", "spawn": [{"agent": _agent("child", tier=tier), "objective": "Review {{parent_output}}"}], "order": 0}]


def test_blocked_spawn_is_denied_but_parent_succeeds(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "done", "usage": {}}]])
    monkeypatch.setitem(registry, "fake", fake)
    monkeypatch.setattr(governance, "effective_blocked_tiers", lambda level=None: ["network"])
    run_id = _run()

    list(workflow_exec.run_workflow(_ir(tier="network"), stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))

    assert runtime_state.read_run(run_id)["status"] == "succeeded"
    assert len(runtime_state.list_runs()) == 1
    assert "risk_tier 'network' blocked for agent 'child'" in governance.status()["recent_denials"][0]["reasons"]


def test_allowed_child_succeeds_and_appends_claim(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([
        [{"type": "delta", "text": "parent output"}, {"type": "done", "usage": {}}],
        [{"type": "delta", "text": "child output"}, {"type": "done", "usage": {}}],
    ])
    monkeypatch.setitem(registry, "fake", fake)
    run_id = _run()

    list(workflow_exec.run_workflow(_ir(), stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))

    parent = runtime_state.read_run(run_id)
    child_id = parent["child_runs"][0]["run_id"]
    assert parent["status"] == "succeeded"
    assert runtime_state.read_run(child_id)["status"] == "succeeded"
    claim = json.loads(runtime_state.runtime_path("run", run_id, "artifacts", "claims.jsonl").read_text(encoding="utf-8"))
    assert claim["output"] == "child output"
    assert parent["metadata"]["node_outputs"]["parent_claims"] == "child output"


def test_failed_child_does_not_fail_parent(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([
        [{"type": "done", "usage": {}}],
        [{"type": "error", "message": "child upstream failed"}],
    ])
    monkeypatch.setitem(registry, "fake", fake)
    run_id = _run()

    list(workflow_exec.run_workflow(_ir(), stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))

    parent = runtime_state.read_run(run_id)
    assert parent["status"] == "succeeded"
    assert runtime_state.read_run(parent["child_runs"][0]["run_id"])["status"] == "failed"
    assert not runtime_state.runtime_path("run", run_id, "artifacts", "claims.jsonl").exists()


def test_reject_gate_fails_without_calling_provider(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "done", "usage": {}}]])
    monkeypatch.setitem(registry, "fake", fake)
    run_id = _run()
    ir = [{"id": "gate", "agent": _agent("lead"), "prompt": "Do {{objective}}", "gate": "approval", "spawn": [], "order": 0}]

    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))
    interrupt = runtime_state.read_run(run_id)["interrupts"][0]
    runtime_interrupts.resolve_interrupt(run_id, interrupt["interrupt_id"], action="reject")
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))

    state = runtime_state.read_run(run_id)
    assert state["status"] == "failed"
    assert state["metadata"]["error"] == "rejected at gate:gate"
    assert fake.messages == []
