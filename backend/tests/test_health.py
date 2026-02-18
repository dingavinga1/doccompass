from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ok(monkeypatch):
    monkeypatch.setattr("app.main.db_healthcheck", lambda: True)
    monkeypatch.setattr("app.main.redis_healthcheck", lambda: True)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_degraded(monkeypatch):
    monkeypatch.setattr("app.main.db_healthcheck", lambda: False)
    monkeypatch.setattr("app.main.redis_healthcheck", lambda: True)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
