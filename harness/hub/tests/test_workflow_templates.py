from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest
import yaml

import config
from services import runtime_agents, runtime_events, runtime_interrupts, runtime_state, workflow, workflow_exec
from services.providers import registry


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "workflows"
AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"


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

    def stream_chat(self, messages: list[dict[str, str]], session_id: str | None = None, model: str | None = None, **_: Any) -> Iterator[dict[str, Any]]:
        yield from self.scripts.pop(0)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_all_workflow_templates_validate_and_build_ir() -> None:
    for path in sorted(TEMPLATES_DIR.glob("*.workflow.yaml")):
        data = workflow.parse_workflow(path.read_text(encoding="utf-8"))
        assert workflow.validate_workflow(data) == [], path.name
        assert workflow.build_ir(data)


def test_all_agent_profiles_validate() -> None:
    for path in sorted(AGENTS_DIR.glob("*.agent.yaml")):
        runtime_agents.validate_agent_profile(_read_yaml(path))


def test_template_agents_resolve_to_expected_providers() -> None:
    expected = {"drafter": "nvidia", "thinker": "claude", "coder": "codex"}
    agents = {agent["id"]: agent for agent in runtime_agents.list_agents()}
    assert {agent_id: runtime_agents.resolve_provider(agents[agent_id])["provider"] for agent_id in expected} == expected


def test_research_draft_review_fake_provider_passes_and_interrupts(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(config.MODEL_CLASS_ROUTING, "cheap", {"provider": "fake", "model": None})
    monkeypatch.setitem(config.MODEL_CLASS_ROUTING, "smart", {"provider": "fake", "model": None})
    monkeypatch.setitem(registry, "fake", FakeProvider([
        [{"type": "delta", "text": "A useful research draft with enough concrete detail to satisfy the quality gate. " * 5}, {"type": "done", "usage": {}}],
        [{"type": "delta", "text": "Refined research brief."}, {"type": "done", "usage": {}}],
    ]))

    list(workflow_exec.create_workflow_run_stream("research-draft-review", "compare two approaches"))
    run_id = _latest_run_id()
    state = runtime_state.read_run(run_id)
    assert state["status"] == "interrupted"
    assert any(event["type"] == "validation_pass" for event in runtime_events.read_events(run_id))
    interrupt = state["interrupts"][0]
    list(workflow_exec.resume_workflow_run_stream(run_id, interrupt["interrupt_id"], {"action": "resume"}))
    assert runtime_state.read_run(run_id)["status"] == "succeeded"

    monkeypatch.setitem(registry, "fake", FakeProvider([[{"type": "delta", "text": "too short"}, {"type": "done", "usage": {}}]]))
    list(workflow_exec.create_workflow_run_stream("research-draft-review", "test failing quality gate"))
    failed_run_id = _latest_run_id()
    failed_state = runtime_state.read_run(failed_run_id)
    assert failed_state["status"] == "interrupted"
    assert failed_state["interrupts"][0]["payload"]["violations"]


def test_code_task_workspace_write_waits_for_implement_approval(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(config.MODEL_CLASS_ROUTING, "smart", {"provider": "fake", "model": None})
    monkeypatch.setitem(config.MODEL_CLASS_ROUTING, "code", {"provider": "fake", "model": None})
    monkeypatch.setitem(registry, "fake", FakeProvider([
        [{"type": "delta", "text": "Brief with acceptance criteria."}, {"type": "done", "usage": {}}],
        [{"type": "delta", "text": "Implementation complete."}, {"type": "done", "usage": {}}],
        [{"type": "delta", "text": "Review passed."}, {"type": "done", "usage": {}}],
    ]))

    list(workflow_exec.create_workflow_run_stream("code-task", "add safety fix"))
    run_id = _latest_run_id()
    state = runtime_state.read_run(run_id)
    assert state["status"] == "interrupted"
    assert state["metadata"]["completed_nodes"] == ["brief"]
    interrupt = next(item for item in state["interrupts"] if item["status"] == "pending")
    assert interrupt["node"] == "implement"
    assert "Brief with acceptance criteria." in interrupt["payload"]["prompt"]
    assert workflow_exec._load_workflow("code-task")[1][1]["agent"]["permission"] == "workspace_write"

    list(workflow_exec.resume_workflow_run_stream(run_id, interrupt["interrupt_id"], {"action": "resume"}))
    state = runtime_state.read_run(run_id)
    assert state["status"] == "interrupted"
    assert state["metadata"]["completed_nodes"] == ["brief", "implement"]
    review_interrupt = next(item for item in state["interrupts"] if item["status"] == "pending")
    assert review_interrupt["node"] == "review"

    list(workflow_exec.resume_workflow_run_stream(run_id, review_interrupt["interrupt_id"], {"action": "resume"}))
    assert runtime_state.read_run(run_id)["status"] == "succeeded"


def _latest_run_id() -> str:
    runs = sorted(config.RUNTIME_RUNS_DIR.glob("run-*/run.json"), key=lambda path: path.stat().st_mtime)
    return runs[-1].parent.name
