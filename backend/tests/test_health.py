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


def test_readiness_ok(monkeypatch):
    monkeypatch.setattr("app.main.db_healthcheck", lambda: True)
    monkeypatch.setattr("app.main.redis_healthcheck", lambda: True)
    monkeypatch.setattr("app.main.pgvector_healthcheck", lambda: (True, None))

    client = TestClient(create_app())
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["services"]["pgvector"] == "ok"


def test_readiness_degraded_when_pgvector_missing(monkeypatch):
    monkeypatch.setattr("app.main.db_healthcheck", lambda: True)
    monkeypatch.setattr("app.main.redis_healthcheck", lambda: True)
    monkeypatch.setattr(
        "app.main.pgvector_healthcheck",
        lambda: (False, "PGVector extension 'vector' is not installed in the target database."),
    )

    client = TestClient(create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["services"]["pgvector"] == "down"
    assert "details" in response.json()
