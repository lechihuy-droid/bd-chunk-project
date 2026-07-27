from fastapi.testclient import TestClient

from tests.test_api import client


def test_v3_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="root"' in response.text


def test_health_regression(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
