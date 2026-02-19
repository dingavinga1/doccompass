import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import create_app


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.create_all(engine)


def override_get_session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def test_ingestion_api_start_status_stop(monkeypatch, client: TestClient):
    monkeypatch.setattr("app.services.ingestion.celery_app.send_task", lambda *args, **kwargs: None)

    start_response = client.post(
        "/documentation/ingestion",
        json={
            "web_url": "https://example.com",
            "crawl_depth": 2,
            "include_patterns": ["https://example.com*"],
            "exclude_patterns": [],
        },
    )

    assert start_response.status_code == 202
    payload = start_response.json()
    assert payload["status"] == "PENDING"

    status_response = client.get(f"/documentation/ingestion/{payload['job_id']}")
    assert status_response.status_code == 200
    assert status_response.json()["job_id"] == payload["job_id"]

    stop_response = client.post("/documentation/ingestion/stop", json={"job_id": payload["job_id"]})
    assert stop_response.status_code == 200
    assert stop_response.json()["stop_requested"] is True


def test_list_ingestion_jobs(monkeypatch, client: TestClient):
    monkeypatch.setattr("app.services.ingestion.celery_app.send_task", lambda *args, **kwargs: None)

    # Create a few jobs
    for i in range(5):
        client.post(
            "/documentation/ingestion",
            json={
                "web_url": f"https://example.com/{i}",
                "crawl_depth": 2,
            },
        )

    # Test listing all
    response = client.get("/documentation/ingestion")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 5
    assert data["total"] >= 5

    # Test pagination
    response = client.get("/documentation/ingestion?limit=2&skip=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2

    # Test filtering (mocking status change would be needed, or just filter by PENDING which they all are)
    response = client.get("/documentation/ingestion?status=PENDING")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 5
    for item in data["items"]:
        assert item["status"] == "PENDING"
