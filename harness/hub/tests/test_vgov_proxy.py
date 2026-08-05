from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

import config
import server


@pytest.mark.parametrize(
    "path",
    [
        "runs",
        "releases",
        "artifacts",
        "revisions/11111111-1111-1111-1111-111111111111/lineage",
        "explain-difference",
    ],
)
def test_vgov_proxy_preserves_api_vgov_prefix_for_every_functional_route(monkeypatch, path: str) -> None:
    """Regression guard for the prefix-dropping bug: vgov-api mounts every functional router under
    /api/vgov, so forwarding to bare /{path} 404'd runs, releases, artifacts, lineage and
    explain-difference alike, even though the proxy itself answered 200/201."""
    seen: dict[str, object] = {}

    async def request(self, method, url, **kwargs):
        seen.update(method=method, url=url, **kwargs)
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(config, "VGOV_BASE_URL", "http://vgov.test")
    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    client = TestClient(server.app)
    response = client.get(f"/api/vgov/{path}")
    assert response.status_code == 200
    assert seen["url"] == f"http://vgov.test/api/vgov/{path}"


def test_vgov_proxy_forwards_query_string_and_actor_header(monkeypatch) -> None:
    seen: dict[str, object] = {}

    async def request(self, method, url, **kwargs):
        seen.update(method=method, url=url, **kwargs)
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(config, "VGOV_BASE_URL", "http://vgov.test")
    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    client = TestClient(server.app)
    response = client.get(
        "/api/vgov/runs?project_key=demo&workflow_id=wf-1",
        headers={"X-Actor": "reviewer"},
    )
    assert response.status_code == 200
    assert seen["url"] == "http://vgov.test/api/vgov/runs"
    assert dict(seen["params"]) == {"project_key": "demo", "workflow_id": "wf-1"}
    assert seen["headers"]["x-actor"] == "reviewer"


def test_vgov_proxy_forwards_request_and_response(monkeypatch) -> None:
    seen: dict[str, object] = {}

    async def request(self, method, url, **kwargs):
        seen.update(method=method, url=url, **kwargs)
        return httpx.Response(201, json={"ok": True})

    monkeypatch.setattr(config, "VGOV_BASE_URL", "http://vgov.test")
    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    client = TestClient(server.app, headers={"x-hub-client": "harness-hub"})
    response = client.post("/api/vgov/runs?project_key=demo", content=b'{"x":1}', headers={"X-Actor": "tester", "Content-Type": "application/json"})
    assert response.status_code == 201 and response.json() == {"ok": True}
    # vgov-api mounts everything under /api/vgov; dropping the prefix 404s every functional route.
    assert seen["method"] == "POST" and seen["url"] == "http://vgov.test/api/vgov/runs"
    assert seen["content"] == b'{"x":1}' and seen["headers"] == {"x-actor": "tester", "content-type": "application/json"}


def test_vgov_proxy_returns_502_when_upstream_is_down(monkeypatch) -> None:
    async def request(self, method, url, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx.AsyncClient, "request", request)
    response = TestClient(server.app).get("/api/vgov/health")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "RUNTIME_UNAVAILABLE"
