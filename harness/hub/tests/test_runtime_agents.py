from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server
from services import risk, runtime_agents


@pytest.fixture()
def agents_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    agents_dir = tmp_path / "agents"
    monkeypatch.setattr(runtime_agents, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(runtime_agents.skill_library, "list_skills", lambda: [{"name": "opus-design-reviewer"}])
    return agents_dir


def valid_profile() -> dict[str, object]:
    return {
        "id": "reviewer",
        "provider": "claude",
        "model": None,
        "system_prompt": "You are a strict reviewer.",
        "skills": ["opus-design-reviewer"],
        "permission": "read_only",
        "budget": {"seconds": 900, "max_calls": 5},
        "risk_tier": "read_only",
    }


def test_list_agents_loads_valid_yaml(agents_tmp: Path) -> None:
    runtime_agents.create_or_update_agent(valid_profile())

    agents = runtime_agents.list_agents()

    assert agents == [valid_profile()]


@pytest.mark.parametrize(
    ("model_class", "provider"),
    [("cheap", "nvidia"), ("code", "codex"), ("smart", "claude")],
)
def test_resolve_provider_maps_model_classes(model_class: str, provider: str) -> None:
    agent = valid_profile() | {"provider": model_class, "model": "explicit-model"}

    assert runtime_agents.resolve_provider(agent) == {
        "provider": provider,
        "model": "explicit-model",
        "class": model_class,
    }


def test_resolve_provider_preserves_real_provider() -> None:
    agent = valid_profile()

    assert runtime_agents.resolve_provider(agent) == {"provider": "claude", "model": None, "class": None}


def test_validate_agent_profile_accepts_model_class(agents_tmp: Path) -> None:
    runtime_agents.validate_agent_profile(valid_profile() | {"provider": "cheap"})


def test_validate_agent_profile_rejects_unknown_field(agents_tmp: Path) -> None:
    with pytest.raises(ValueError, match="Unknown agent profile field\\(s\\): allowd_tools"):
        runtime_agents.validate_agent_profile(valid_profile() | {"allowd_tools": ["Read"]})


def test_list_agents_preserves_authored_model_class(agents_tmp: Path) -> None:
    profile = valid_profile() | {"provider": "cheap"}
    runtime_agents.create_or_update_agent(profile)

    assert runtime_agents.list_agents() == [profile]


def test_list_agents_skips_invalid_yaml(agents_tmp: Path) -> None:
    invalid = valid_profile() | {"provider": "unknown"}
    agents_tmp.mkdir()
    (agents_tmp / "invalid.agent.yaml").write_text("provider: unknown\n", encoding="utf-8")

    assert runtime_agents.list_agents() == []


@pytest.mark.parametrize(
    ("profile", "message"),
    [
        (valid_profile() | {"provider": "unknown"}, "Unknown provider: unknown"),
        (valid_profile() | {"skills": ["unknown-skill"]}, "Unknown skill: unknown-skill"),
        (valid_profile() | {"budget": {"seconds": 0, "max_calls": 5}}, "budget.seconds must be a positive integer"),
        (valid_profile() | {"budget": {"seconds": 5, "max_calls": -1}}, "budget.max_calls must be a positive integer"),
        ({key: value for key, value in valid_profile().items() if key != "risk_tier"}, "Missing required field: risk_tier"),
        (valid_profile() | {"id": "nested/reviewer"}, "Invalid agent id: nested/reviewer"),
        (valid_profile() | {"id": "..reviewer"}, "Invalid agent id: ..reviewer"),
    ],
)
def test_validate_agent_profile_rejects_invalid_profiles(
    agents_tmp: Path, profile: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        runtime_agents.validate_agent_profile(profile)


def test_agent_profile_api_crud(agents_tmp: Path) -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    profile = valid_profile()

    created = client.post("/api/agents", json=profile)
    assert created.status_code == 200
    assert created.json() == profile
    assert (agents_tmp / "reviewer.agent.yaml").is_file()

    listed = client.get("/api/agents")
    assert listed.status_code == 200
    assert listed.json() == [profile]

    invalid = client.post("/api/agents", json=profile | {"provider": "unknown"})
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Unknown provider: unknown; valid providers or model classes: cheap, code, smart"

    deleted = client.delete("/api/agents/reviewer")
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}
    assert not (agents_tmp / "reviewer.agent.yaml").exists()

    missing = client.delete("/api/agents/missing")
    assert missing.status_code == 404


def test_agent_profile_api_rejects_tier_outside_blocklist_vocabulary(agents_tmp: Path) -> None:
    """Spawn gating matches risk_tier by exact string, so a tier that is not in
    risk.TIERS can never be blocked and would bypass every governance level."""
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})

    rejected = client.post("/api/agents", json=valid_profile() | {"risk_tier": "low"})
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == (
        "Invalid risk_tier: low; valid tiers: read_only, write, execute, network, destructive"
    )
    assert not (agents_tmp / "reviewer.agent.yaml").exists()

    accepted = client.post("/api/agents", json=valid_profile() | {"risk_tier": "destructive"})
    assert accepted.status_code == 200
    assert accepted.json()["risk_tier"] == "destructive"


def test_risk_tiers_endpoint_serves_the_canonical_list() -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})

    response = client.get("/api/risk-tiers")
    assert response.status_code == 200
    assert response.json() == risk.TIERS


def test_model_classes_api() -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})

    response = client.get("/api/model-classes")

    assert response.status_code == 200
    assert response.json() == {
        "cheap": {"provider": "nvidia", "model": None},
        "code": {"provider": "codex", "model": None},
        "smart": {"provider": "claude", "model": None},
    }
