from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import config
import server
from services import runtime_agents, runtime_artifacts, skill_library, workflow


def test_search_returns_real_cross_type_matches(monkeypatch, tmp_path: Path) -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    monkeypatch.setattr(workflow, "list_workflows", lambda: [{"id": "needle-flow", "nodes": []}])
    monkeypatch.setattr(runtime_agents, "list_agents", lambda: [{"id": "needle-agent", "provider": "nvidia", "system_prompt": ""}])
    monkeypatch.setattr(runtime_artifacts, "list_library_artifacts", lambda: [{"id": "needle-artifact", "title": "needle artifact", "source": "chat"}])
    monkeypatch.setattr(config, "SKILL_SOURCES", {"local": tmp_path / "skills"}, raising=False)
    path = tmp_path / "skills" / "needle-skill" / "SKILL.md"; path.parent.mkdir(parents=True); path.write_text("---\nname: needle skill\ndescription: indexed needle\n---\n", encoding="utf-8")
    skill_library._clear_cache()

    response = client.get("/api/search", params={"q": "needle"})

    assert response.status_code == 200
    assert {(item["type"], item["id"]) for item in response.json()} == {("workflow", "needle-flow"), ("agent", "needle-agent"), ("skill", "local/needle-skill"), ("artifact", "needle-artifact")}
    assert all(set(item) == {"type", "id", "title", "context", "href"} for item in response.json())


def test_search_short_or_missing_query_is_empty() -> None:
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    assert client.get("/api/search", params={"q": "n"}).json() == []
    assert client.get("/api/search", params={"q": "absent-search-value"}).json() == []
