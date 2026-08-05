from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

import config
from services import risk, skill_library
from services.providers import registry


LOGGER = logging.getLogger(__name__)
AGENTS_DIR = config.HUB_DIR / "agents"
REQUIRED_FIELDS = ("id", "provider", "system_prompt", "skills", "permission", "budget", "risk_tier")
OPTIONAL_FIELDS = ("model", "allowed_tools", "allowed_paths")
PROFILE_FIELDS = frozenset((*REQUIRED_FIELDS, *OPTIONAL_FIELDS))
PERMISSIONS = {"read_only", "workspace_write"}


def _validate_agent_id(agent_id: object) -> str:
    if not isinstance(agent_id, str) or not agent_id or "/" in agent_id or "\\" in agent_id or ".." in agent_id:
        raise ValueError(f"Invalid agent id: {agent_id}")
    return agent_id


def validate_agent_profile(data: dict[str, Any], known_skills: set[str] | None = None) -> None:
    if not isinstance(data, dict):
        raise ValueError("Agent profile must be a mapping")
    unknown = sorted(set(data) - PROFILE_FIELDS)
    if unknown:
        raise ValueError(f"Unknown agent profile field(s): {', '.join(unknown)}")

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    _validate_agent_id(data["id"])

    provider = data["provider"]
    if provider not in registry and provider not in config.MODEL_CLASS_ROUTING:
        classes = ", ".join(sorted(config.MODEL_CLASS_ROUTING))
        raise ValueError(f"Unknown provider: {provider}; valid providers or model classes: {classes}")

    skills = data["skills"]
    if not isinstance(skills, list):
        raise ValueError("skills must be a list")
    if known_skills is None:
        known_skills = skill_library.list_skill_names()
    for skill in skills:
        if skill not in known_skills:
            raise ValueError(f"Unknown skill: {skill}")

    permission = data["permission"]
    if permission not in PERMISSIONS:
        raise ValueError(f"Invalid permission: {permission}")

    for field in ("allowed_tools", "allowed_paths"):
        value = data.get(field)
        if value is not None and (not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value)):
            raise ValueError(f"{field} must be a list of non-empty strings")

    # Spawn gating matches the tier by exact string (workflow_exec), so a tier
    # outside risk.TIERS can never appear in a blocklist and would silently
    # bypass every governance level.
    risk_tier = data["risk_tier"]
    if risk_tier not in risk.TIERS:
        valid = ", ".join(risk.TIERS)
        raise ValueError(f"Invalid risk_tier: {risk_tier}; valid tiers: {valid}")

    budget = data["budget"]
    if not isinstance(budget, dict):
        raise ValueError("budget must be a mapping")
    if not isinstance(budget.get("seconds"), int) or isinstance(budget["seconds"], bool) or budget["seconds"] <= 0:
        raise ValueError("budget.seconds must be a positive integer")
    if not isinstance(budget.get("max_calls"), int) or isinstance(budget["max_calls"], bool) or budget["max_calls"] <= 0:
        raise ValueError("budget.max_calls must be a positive integer")


def resolve_provider(agent: dict[str, Any]) -> dict[str, Any]:
    authored_provider = agent["provider"]
    route = config.MODEL_CLASS_ROUTING.get(authored_provider)
    if route is None:
        if authored_provider not in registry:
            classes = ", ".join(sorted(config.MODEL_CLASS_ROUTING))
            raise ValueError(f"Unknown provider: {authored_provider}; valid providers or model classes: {classes}")
        return {"provider": authored_provider, "model": agent.get("model"), "class": None}
    return {
        "provider": route["provider"],
        "model": agent.get("model") if agent.get("model") is not None else route.get("model"),
        "class": authored_provider,
    }


def list_agents() -> list[dict[str, Any]]:
    if not AGENTS_DIR.exists():
        return []

    known_skills = skill_library.list_skill_names()
    agents: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in sorted(AGENTS_DIR.glob("*.agent.yaml"), key=lambda item: item.name.lower()):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            validate_agent_profile(data, known_skills)
            agent_id = str(data["id"])
            if agent_id in seen_ids:
                LOGGER.warning("Skipping duplicate agent profile id %r in %s", agent_id, path)
                continue
        except (OSError, ValueError, yaml.YAMLError) as exc:
            LOGGER.warning("Skipping invalid agent profile %s: %s", path, exc)
            continue
        seen_ids.add(agent_id)
        agents.append(data)
    return agents


def get_agent(agent_id: str) -> dict[str, Any]:
    for agent in list_agents():
        if agent["id"] == agent_id:
            return dict(agent)
    raise FileNotFoundError(f"Agent not found: {agent_id}")


def create_or_update_agent(data: dict[str, Any]) -> dict[str, Any]:
    validate_agent_profile(data)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = AGENTS_DIR / f"{data['id']}.agent.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return data


def delete_agent(agent_id: str) -> None:
    _validate_agent_id(agent_id)
    path = AGENTS_DIR / f"{agent_id}.agent.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    path.unlink()
