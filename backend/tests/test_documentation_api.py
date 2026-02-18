import urllib.parse
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import create_app
from app.models import Documentation, DocumentationSection, IngestionJob, IngestionStatus, RawPage


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


def _reset_data() -> None:
    with Session(engine) as session:
        for model in [DocumentationSection, IngestionJob, RawPage, Documentation]:
            for row in session.exec(select(model)).all():
                session.delete(row)
        session.commit()


def _seed_doc() -> uuid.UUID:
    with Session(engine) as session:
        doc = Documentation(url="https://docs.example.com", title="Example Docs", crawl_depth=2)
        session.add(doc)
        session.commit()
        session.refresh(doc)

        section_a = DocumentationSection(
            documentation_id=doc.id,
            path="/guide",
            title="Guide",
            summary="Root guide",
            content="Guide content",
            level=1,
            token_count=2,
            checksum="a",
        )
        session.add(section_a)
        session.flush()
        section_b = DocumentationSection(
            documentation_id=doc.id,
            path="/guide/intro",
            parent_id=section_a.id,
            title="Router Intro",
            summary="intro router",
            content="router in intro section",
            level=2,
            token_count=4,
            checksum="b",
        )
        section_c = DocumentationSection(
            documentation_id=doc.id,
            path="/guide/advanced",
            title="Advanced",
            summary="deep topic",
            content="content with router details",
            level=2,
            token_count=4,
            checksum="c",
        )
        session.add(section_b)
        session.add(section_c)

        job = IngestionJob(documentation_id=doc.id, status=IngestionStatus.COMPLETED)
        raw = RawPage(documentation_id=doc.id, url="https://docs.example.com/page", markdown_content="# Guide")
        session.add(job)
        session.add(raw)
        session.commit()

        return doc.id


def test_documentation_list_pagination(client: TestClient):
    _reset_data()
    first_id = _seed_doc()
    with Session(engine) as session:
        session.add(Documentation(url="https://docs.example.com/2", title="Docs 2", crawl_depth=1))
        session.commit()

    response = client.get("/documentation", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] != str(first_id)


def test_sections_list_with_start_path(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()

    response = client.get(f"/documentation/{doc_id}", params={"start_path": "/guide/intro"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["path"] == "/guide/intro"


def test_get_section_content_success_and_404(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()

    encoded = urllib.parse.quote("/guide/intro", safe="")
    response = client.get(f"/documentation/{doc_id}/sections/{encoded}")
    assert response.status_code == 200
    assert response.json()["path"] == "/guide/intro"

    missing = client.get(f"/documentation/{doc_id}/sections/{urllib.parse.quote('/missing', safe='')}")
    assert missing.status_code == 404


def test_get_tree_structure_ordering(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()
    with Session(engine) as session:
        orphan = DocumentationSection(
            documentation_id=doc_id,
            path="/guide/intro/install",
            title="Install",
            level=3,
            checksum="z",
        )
        session.add(orphan)
        session.commit()

    response = client.get(f"/documentation/{doc_id}/tree")
    assert response.status_code == 200
    roots = response.json()["roots"]
    assert roots[0]["path"] == "/guide"
    child_paths = [child["path"] for child in roots[0]["children"]]
    assert "/guide/advanced" in child_paths
    assert "/guide/intro" in child_paths


def test_keyword_search_relevance_and_mode(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()

    response = client.get(f"/documentation/{doc_id}/search", params={"q": "router"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["search_mode"] == "keyword_fallback"
    assert len(payload["items"]) >= 2
    assert payload["items"][0]["score"] >= payload["items"][1]["score"]


def test_delete_documentation_cascade(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()

    response = client.delete(f"/documentation/{doc_id}")
    assert response.status_code == 204

    check = client.get(f"/documentation/{doc_id}")
    assert check.status_code == 404

    with Session(engine) as session:
        assert session.exec(select(func.count()).select_from(DocumentationSection)).one() == 0
        assert session.exec(select(func.count()).select_from(IngestionJob)).one() == 0
        assert session.exec(select(func.count()).select_from(RawPage)).one() == 0


def test_validation_errors(client: TestClient):
    _reset_data()
    doc_id = _seed_doc()

    short_query = client.get(f"/documentation/{doc_id}/search", params={"q": "a"})
    assert short_query.status_code == 422

    bad_limit = client.get(f"/documentation/{doc_id}", params={"limit": 0})
    assert bad_limit.status_code == 422

    bad_id = client.get("/documentation/not-a-uuid")
    assert bad_id.status_code == 422
