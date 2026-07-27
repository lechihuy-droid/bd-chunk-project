from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest

import config
from services import runtime_artifacts, runtime_interrupts, runtime_state, runtime_validate, workflow, workflow_exec
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
        self.calls = 0

    def stream_chat(self, messages: list[dict[str, str]], session_id: str | None = None, model: str | None = None) -> Iterator[dict[str, Any]]:
        self.calls += 1
        yield {"type": "delta", "text": self.text}
        yield {"type": "done", "usage": {}}


def _agent() -> dict[str, Any]:
    return {
        "id": "reviewer", "provider": "fake", "model": None, "system_prompt": "Review.",
        "budget": {"seconds": 60, "max_calls": 5}, "skills": [], "permission": "read_only", "risk_tier": "read_only",
    }


def _run() -> str:
    return str(runtime_state.create_run(agent_id="lead", metadata={"objective": "ship"})["run_id"])


def _workflow_data(validate_node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "validation",
        "nodes": [{"id": "draft", "agent": "reviewer", "prompt": "Draft", "gate": "none"}, validate_node],
        "edges": [["draft", validate_node["id"]]],
        "stop": {"max_nodes": 5, "max_seconds": 60},
    }


def test_run_checks_all_supported_kinds_and_unknown_kind() -> None:
    assert runtime_validate.run_checks("abcdef", [{"kind": "min_length", "value": 3}]) == []
    assert runtime_validate.run_checks("abcdef", [{"kind": "must_include", "values": ["bc"]}]) == []
    assert runtime_validate.run_checks("abcdef", [{"kind": "must_not_include", "values": ["zz"]}]) == []
    assert runtime_validate.run_checks('{"ok": true}', [{"kind": "json_parseable"}]) == []
    violations = runtime_validate.run_checks("abc", [
        {"kind": "min_length", "value": 4},
        {"kind": "must_include", "values": ["xyz"]},
        {"kind": "must_not_include", "values": ["b"]},
        {"kind": "json_parseable"},
        {"kind": "future_check"},
    ])
    assert [item["kind"] for item in violations] == ["min_length", "must_include", "must_not_include", "json_parseable", "future_check"]


def test_validate_workflow_and_build_ir_support_validate_node(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workflow.runtime_agents, "list_agents", lambda: [{"id": "reviewer"}])
    data = _workflow_data({"id": "check_draft", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 2}], "on_fail": "interrupt"})
    assert workflow.validate_workflow(data) == []
    assert workflow.build_ir(data)[1] == {"id": "check_draft", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 2}], "on_fail": "interrupt", "order": 1}


@pytest.mark.parametrize("change", [
    lambda node: node.update(target="missing"),
    lambda node: node.update(on_fail="pause"),
    lambda node: node.update(checks=[{"kind": "min_length", "value": "long"}]),
    lambda node: node.update(checks=[{"kind": "must_include", "values": []}]),
])
def test_validate_workflow_rejects_bad_validate_nodes(monkeypatch: pytest.MonkeyPatch, change) -> None:
    monkeypatch.setattr(workflow.runtime_agents, "list_agents", lambda: [{"id": "reviewer"}])
    validate_node = {"id": "check_draft", "type": "validate", "target": "draft", "checks": [{"kind": "json_parseable"}], "on_fail": "fail"}
    change(validate_node)
    errors = workflow.validate_workflow(_workflow_data(validate_node))
    assert errors


def test_validate_fail_marks_run_failed_and_emits_violations(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider("short")
    monkeypatch.setitem(registry, "fake", fake)
    run_id = _run()
    ir = [{"id": "draft", "agent": _agent(), "prompt": "Draft", "gate": "none", "order": 0}, {"id": "check", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 99}], "on_fail": "fail", "order": 1}]
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    state = runtime_state.read_run(run_id)
    assert state["status"] == "failed"
    assert any(event["type"] == "validation_fail" and event["violations"] for event in _events(run_id))
    assert fake.calls == 1


def test_validate_interrupt_resume_skips_checks_and_succeeds(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider("short")
    monkeypatch.setitem(registry, "fake", fake)
    run_id = _run()
    ir = [{"id": "draft", "agent": _agent(), "prompt": "Draft", "gate": "none", "order": 0}, {"id": "check", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 99}], "on_fail": "interrupt", "order": 1}]
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    interrupt = runtime_state.read_run(run_id)["interrupts"][0]
    assert interrupt["status"] == "pending" and interrupt["payload"]["violations"]
    runtime_interrupts.resolve_interrupt(run_id, interrupt["interrupt_id"], action="resume")
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    state = runtime_state.read_run(run_id)
    assert state["status"] == "succeeded"
    assert state["metadata"]["completed_nodes"] == ["draft", "check"]


def test_validate_interrupt_reject_fails(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(registry, "fake", FakeProvider("short"))
    run_id = _run()
    ir = [{"id": "draft", "agent": _agent(), "prompt": "Draft", "gate": "none", "order": 0}, {"id": "check", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 99}], "on_fail": "interrupt", "order": 1}]
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    interrupt = runtime_state.read_run(run_id)["interrupts"][0]
    runtime_interrupts.resolve_interrupt(run_id, interrupt["interrupt_id"], action="reject")
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    assert runtime_state.read_run(run_id)["status"] == "failed"


def test_validate_happy_path_counts_node_and_emits_pass(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(registry, "fake", FakeProvider("long enough"))
    run_id = _run()
    ir = [{"id": "draft", "agent": _agent(), "prompt": "Draft", "gate": "none", "order": 0}, {"id": "check", "type": "validate", "target": "draft", "checks": [{"kind": "min_length", "value": 2}], "on_fail": "fail", "order": 1}]
    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))
    state = runtime_state.read_run(run_id)
    assert state["status"] == "succeeded"
    assert state["metadata"]["completed_nodes"] == ["draft", "check"]
    assert any(event["type"] == "validation_pass" for event in _events(run_id))


def test_validate_uses_metadata_output_when_artifact_is_missing(runtime_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeProvider("fallback text")
    monkeypatch.setitem(registry, "fake", fake)
    monkeypatch.setattr(runtime_artifacts, "read_artifact", lambda *_args: (_ for _ in ()).throw(FileNotFoundError()))
    checked: list[str] = []
    original_run_checks = runtime_validate.run_checks

    def capture(text: str, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        checked.append(text)
        return original_run_checks(text, checks)

    monkeypatch.setattr(runtime_validate, "run_checks", capture)
    run_id = _run()
    ir = [
        {"id": "draft", "agent": _agent(), "prompt": "Draft", "gate": "none", "order": 0},
        {"id": "check", "type": "validate", "target": "draft", "checks": [{"kind": "must_include", "values": ["fallback"]}], "on_fail": "fail", "order": 1},
    ]

    list(workflow_exec.run_workflow(ir, stop={"max_nodes": 5, "max_seconds": 60}, objective="ship", run_id=run_id))

    assert checked == ["fallback text"]


def _events(run_id: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (runtime_state.run_dir(run_id) / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def test_artifact_read_rejects_direct_traversal(runtime_tmp: Path) -> None:
    run_id = _run()
    for name in ("../run.json", "..\\run.json", "/etc/passwd"):
        with pytest.raises(FileNotFoundError):
            runtime_artifacts.read_artifact(run_id, name)


def test_artifact_write_sanitizes_node_id_inside_artifacts(runtime_tmp: Path) -> None:
    run_id = _run()
    rel = runtime_artifacts.write_node_artifact(run_id, "../../evil", "x")
    artifacts_dir = runtime_state.run_dir(run_id) / "artifacts"
    assert (artifacts_dir / Path(rel).name).read_text(encoding="utf-8") == "x"
    assert not (runtime_state.run_dir(run_id).parent / "evil.md").exists()
