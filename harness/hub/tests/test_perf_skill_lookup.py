from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from services import runtime_agents, skill_library, workflow


def _profile(agent_id: str, skill: str = "known-skill") -> dict[str, object]:
    return {
        "id": agent_id,
        "provider": "claude",
        "system_prompt": "Review carefully.",
        "skills": [skill],
        "permission": "read_only",
        "budget": {"seconds": 60, "max_calls": 1},
        "risk_tier": "read_only",
    }


def _workflow(workflow_id: str, agent_id: str = "agent-1") -> dict[str, object]:
    return {
        "id": workflow_id,
        "nodes": [{"id": "step", "agent": agent_id, "prompt": "{{objective}}", "gate": "none"}],
        "edges": [],
        "stop": {"max_nodes": 1, "max_seconds": 60},
    }


def test_validate_agent_profile_preserves_skill_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(skill_library, "list_skill_names", lambda: {"known-skill"})

    runtime_agents.validate_agent_profile(_profile("reviewer"))
    with pytest.raises(ValueError, match="Unknown skill: missing-skill"):
        runtime_agents.validate_agent_profile(_profile("reviewer", "missing-skill"))


def test_list_agents_uses_cheap_skill_lookup_once_and_never_telemetry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for agent_id in ("agent-1", "agent-2", "agent-3"):
        (agents_dir / f"{agent_id}.agent.yaml").write_text(yaml.safe_dump(_profile(agent_id)), encoding="utf-8")
    monkeypatch.setattr(runtime_agents, "AGENTS_DIR", agents_dir)

    name_calls = 0

    def list_names() -> set[str]:
        nonlocal name_calls
        name_calls += 1
        return {"known-skill"}

    def telemetry() -> list[dict[str, object]]:
        raise AssertionError("agent validation must not collect telemetry")

    monkeypatch.setattr(skill_library, "list_skill_names", list_names)
    monkeypatch.setattr(skill_library, "_safe_collect_skill_tool_events", telemetry)

    assert len(runtime_agents.list_agents()) == 3
    assert name_calls == 1


def test_list_workflows_resolves_agents_once_and_skips_invalid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    for workflow_id in ("one", "two", "three"):
        data = _workflow(workflow_id)
        (workflows_dir / f"{workflow_id}.workflow.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    invalid = _workflow("invalid")
    invalid["nodes"][0]["agent"] = "missing-agent"  # type: ignore[index]
    (workflows_dir / "invalid.workflow.yaml").write_text(yaml.safe_dump(invalid), encoding="utf-8")
    monkeypatch.setattr(workflow, "WORKFLOWS_DIR", workflows_dir)

    calls = 0

    def list_agents() -> list[dict[str, str]]:
        nonlocal calls
        calls += 1
        return [{"id": "agent-1"}]

    monkeypatch.setattr(workflow.runtime_agents, "list_agents", list_agents)

    listed = workflow.list_workflows()
    assert [item["id"] for item in listed] == ["one", "three", "two"]
    assert calls == 1

    bad = _workflow("bad")
    bad["nodes"][0]["agent"] = "missing-agent"  # type: ignore[index]
    errors = workflow.validate_workflow(bad)
    assert "Node step references unknown agent: missing-agent" in errors
