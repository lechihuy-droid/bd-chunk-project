from __future__ import annotations

from pathlib import Path

import yaml

import config
from services import runtime_agents, skill_library


EXAMPLE_AGENTS_DIR = config.HUB_DIR / "agents"


def _read_yaml(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_hub_builtin_skill_source_is_discovered() -> None:
    skill_library._clear_cache()
    entries = [entry for entry in skill_library.list_skills() if entry["source"] == "hub_builtin"]

    assert config.SKILL_SOURCES["hub_builtin"] == config.HUB_DIR / "skills"
    assert {entry["name"] for entry in entries} == {
        "backend-patterns",
        "coding-standards",
        "documentation",
        "hub-commit-message",
        "hub-diff-review",
            "hub-run-artifact-summary",
            "remotion-video-map",
            "system-design",
        "tech-debt",
        "testing-strategy",
    }


def test_shipped_agents_validate_and_resolve_their_skills() -> None:
    skill_library._clear_cache()
    known_skills = skill_library.list_skill_names()
    agents = sorted(EXAMPLE_AGENTS_DIR.glob("*.agent.yaml"))

    assert agents
    for path in agents:
        profile = _read_yaml(path)
        runtime_agents.validate_agent_profile(profile, known_skills)
        assert set(profile["skills"]) <= known_skills
