from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import config
from services import runtime_agents, runtime_checkpoint, runtime_interrupts, runtime_state, workflow_exec
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
    def __init__(self, scripts: list[list[dict[str, Any]]]) -> None:
        self.scripts = scripts
        self.messages: list[list[dict[str, str]]] = []

    def status(self) -> dict[str, Any]:
        return {"id": "fake", "available": True}

    def stream_chat(self, messages: list[dict[str, str]], session_id: str | None = None, model: str | None = None) -> Iterator[dict[str, Any]]:
        self.messages.append(messages)
        yield from self.scripts.pop(0)


def _agent(*, max_calls: int = 5) -> dict[str, Any]:
    return {
        "id": "reviewer", "provider": "fake", "model": None, "system_prompt": "Review carefully.",
        "budget": {"seconds": 60, "max_calls": max_calls}, "skills": [], "permission": "read_only", "risk_tier": "read_only",
    }


def _run() -> str:
    return str(runtime_state.create_run(agent_id="lead", metadata={"objective": "ship feature"})["run_id"])


def test_two_node_chain_renders_output_and_checkpoints(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([
        [{"type": "delta", "text": "foo"}, {"type": "delta", "text": "bar"}, {"type": "done", "usage": {"total_tokens": 2}}],
        [{"type": "delta", "text": "done"}, {"type": "done", "usage": {"total_tokens": 3}}],
    ])
    monkeypatch.setitem(registry, "fake", fake)
    ir = [
        {"id": "a", "agent": _agent(), "prompt": "Plan {{objective}}", "gate": "none", "order": 0},
        {"id": "b", "agent": _agent(), "prompt": "Use {{a_output}}", "gate": "none", "order": 1},
    ]
    run_id = _run()

    events = list(workflow_exec.run_workflow(ir, stop={"max_nodes": 2, "max_seconds": 60}, objective="ship feature", run_id=run_id))

    state = runtime_state.read_run(run_id)
    assert state["status"] == "succeeded"
    assert state["metadata"]["node_outputs"] == {"a": "foobar", "b": "done"}
    assert "foobar" in fake.messages[1][1]["content"]
    assert any("event: done" in event for event in events)
    checkpoints = runtime_checkpoint.list_checkpoints(state["thread_id"])
    assert {item["reason"] for item in checkpoints} >= {"node:a", "node:b"}


def test_model_class_routes_to_fake_provider_without_changing_budget(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "delta", "text": "routed"}, {"type": "done", "usage": {}}]])
    monkeypatch.setitem(registry, "fake", fake)
    monkeypatch.setitem(config.MODEL_CLASS_ROUTING, "cheap", {"provider": "fake", "model": None})
    ir = [{"id": "a", "agent": _agent() | {"provider": "cheap"}, "prompt": "A", "gate": "none", "order": 0}]
    run_id = _run()

    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship", run_id=run_id))

    state = runtime_state.read_run(run_id)
    assert state["status"] == "succeeded"
    assert state["metadata"]["agent_calls"] == {"reviewer": 1}
    assert fake.messages


def test_approval_gate_reenters_same_node(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "delta", "text": "approved output"}, {"type": "done", "usage": {}}]])
    monkeypatch.setitem(registry, "fake", fake)
    ir = [{"id": "approve", "agent": _agent(), "prompt": "Do {{objective}}", "gate": "approval", "order": 0}]
    run_id = _run()

    first = list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship feature", run_id=run_id))
    state = runtime_state.read_run(run_id)
    assert any("event: interrupt" in event for event in first)
    assert state["status"] == "interrupted"
    assert state["metadata"]["node_index"] == 0
    assert state["metadata"]["node_outputs"] == {}

    interrupt = state["interrupts"][0]
    runtime_interrupts.resolve_interrupt(run_id, interrupt["interrupt_id"], resume_payload={"approved": True})
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 1, "max_seconds": 60}, objective="ship feature", run_id=run_id))
    state = runtime_state.read_run(run_id)
    assert state["status"] == "succeeded"
    assert state["metadata"]["node_outputs"] == {"approve": "approved output"}


def test_agent_call_budget_stops_before_second_provider_call(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "done", "usage": {}}]])
    monkeypatch.setitem(registry, "fake", fake)
    ir = [
        {"id": "a", "agent": _agent(max_calls=1), "prompt": "A", "gate": "none", "order": 0},
        {"id": "b", "agent": _agent(max_calls=1), "prompt": "B", "gate": "none", "order": 1},
    ]
    run_id = _run()

    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 2, "max_seconds": 60}, objective="ship feature", run_id=run_id))

    state = runtime_state.read_run(run_id)
    assert state["status"] == "failed"
    assert "budget_exceeded: agent max_calls (reviewer)" == state["metadata"]["error"]
    assert len(fake.messages) == 1


def test_provider_error_stops_remaining_nodes(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider([[{"type": "delta", "text": "partial"}, {"type": "error", "message": "upstream failed"}]])
    monkeypatch.setitem(registry, "fake", fake)
    ir = [
        {"id": "bad", "agent": _agent(), "prompt": "Bad", "gate": "none", "order": 0},
        {"id": "never", "agent": _agent(), "prompt": "Never", "gate": "none", "order": 1},
    ]
    run_id = _run()

    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 2, "max_seconds": 60}, objective="ship feature", run_id=run_id))

    state = runtime_state.read_run(run_id)
    assert state["status"] == "failed"
    assert state["metadata"]["error"] == "upstream failed"
    assert state["metadata"]["node_outputs"] == {}
    assert state["metadata"]["completed_nodes"] == []
    assert len(fake.messages) == 1
