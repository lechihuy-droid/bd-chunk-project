from __future__ import annotations

from typing import Any

from services import runtime_agents, runtime_artifacts, skill_library, workflow


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _matches(query: str, *values: object) -> bool:
    return any(query in _text(value).casefold() for value in values)


def search(query: str) -> list[dict[str, str]]:
    query = query.strip().casefold()
    if len(query) < 2:
        return []
    results: list[dict[str, str]] = []
    for item in workflow.list_workflows():
        workflow_id = _text(item.get("id"))
        context = f"{len(item.get('nodes', []))} node" if isinstance(item.get("nodes"), list) else "—"
        if _matches(query, workflow_id, context, str(item.get("nodes"))):
            results.append({"type": "workflow", "id": workflow_id, "title": workflow_id, "context": context, "href": "/workflows"})
    for item in runtime_agents.list_agents():
        agent_id, provider = _text(item.get("id")), _text(item.get("provider"))
        if _matches(query, agent_id, provider, item.get("system_prompt")):
            results.append({"type": "agent", "id": agent_id, "title": agent_id, "context": provider or "—", "href": "/agents"})
    for item in skill_library.list_skills():
        skill_id, name, description = _text(item.get("id")), _text(item.get("name")), _text(item.get("description"))
        if _matches(query, skill_id, name, description):
            results.append({"type": "skill", "id": skill_id, "title": name, "context": description or "—", "href": "/skills"})
    for item in runtime_artifacts.list_library_artifacts():
        artifact_id, title, source = _text(item.get("id")), _text(item.get("title")), _text(item.get("source"))
        if _matches(query, artifact_id, title, source):
            results.append({"type": "artifact", "id": artifact_id, "title": title, "context": source or "—", "href": "/artifacts"})
    return results
