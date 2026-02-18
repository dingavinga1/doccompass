import urllib.parse
import uuid

import pytest
from fastapi.testclient import TestClient
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


def _seed_doc() -> tuple[uuid.UUID, str]:
    with Session(engine) as session:
        doc = Documentation(url="https://docs.example.com", title="Example Docs", crawl_depth=2)
        session.add(doc)
        session.commit()
        session.refresh(doc)

        section = DocumentationSection(
            documentation_id=doc.id,
            path="/guide/intro",
            title="Router Intro",
            summary="intro router",
            content="router in intro section",
            level=2,
            token_count=4,
            checksum="b",
        )
        session.add(section)
        session.add(IngestionJob(documentation_id=doc.id, status=IngestionStatus.COMPLETED))
        session.commit()

        return doc.id, section.path


def _mcp_call(client: TestClient, request_id: int, method: str, params: dict | None = None, token: str | None = None):
    headers = {
        "Accept": "application/json, text/event-stream",
    }
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    return client.post("/mcp", headers=headers, json=payload)


def test_mcp_tools_list_exposes_only_read_only_tools(client: TestClient):
    response = _mcp_call(client, request_id=1, method="tools/list", params={}, token="super-secret-token")
    assert response.status_code == 200
    payload = response.json()

    tool_names = {tool["name"] for tool in payload["result"]["tools"]}
    assert tool_names == {
        "list_documentations",
        "list_documentation_sections",
        "get_section_content",
        "get_documentation_tree",
        "search_documentation",
    }
    assert "delete_documentation_endpoint" not in tool_names
    assert "start_ingestion" not in tool_names


def test_mcp_auth_requires_bearer_token(client: TestClient):
    missing = _mcp_call(client, request_id=2, method="tools/list", params={}, token=None)
    assert missing.status_code == 401
    assert missing.json()["detail"] == "Unauthorized"

    invalid = _mcp_call(client, request_id=3, method="tools/list", params={}, token="wrong-token")
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Unauthorized"

    valid = _mcp_call(client, request_id=4, method="tools/list", params={}, token="super-secret-token")
    assert valid.status_code == 200


def test_mcp_read_only_tool_contracts(client: TestClient):
    _reset_data()
    doc_id, section_path = _seed_doc()

    list_docs = _mcp_call(
        client,
        request_id=5,
        method="tools/call",
        params={"name": "list_documentations", "arguments": {"limit": 20, "offset": 0}},
        token="super-secret-token",
    )
    assert list_docs.status_code == 200
    docs_content = list_docs.json()["result"]["structuredContent"]
    assert docs_content["meta"]["limit"] == 20
    assert docs_content["items"][0]["id"] == str(doc_id)

    list_sections = _mcp_call(
        client,
        request_id=6,
        method="tools/call",
        params={
            "name": "list_documentation_sections",
            "arguments": {"documentation_id": str(doc_id), "start_path": "/guide", "limit": 10, "offset": 0},
        },
        token="super-secret-token",
    )
    assert list_sections.status_code == 200
    sections_content = list_sections.json()["result"]["structuredContent"]
    assert sections_content["meta"]["total"] == 1
    assert sections_content["items"][0]["path"] == section_path

    get_section = _mcp_call(
        client,
        request_id=7,
        method="tools/call",
        params={
            "name": "get_section_content",
            "arguments": {
                "documentation_id": str(doc_id),
                "section_path": urllib.parse.quote(section_path, safe=""),
            },
        },
        token="super-secret-token",
    )
    assert get_section.status_code == 200
    section_content = get_section.json()["result"]["structuredContent"]
    assert section_content["path"] == section_path

    search = _mcp_call(
        client,
        request_id=8,
        method="tools/call",
        params={"name": "search_documentation", "arguments": {"documentation_id": str(doc_id), "q": "router"}},
        token="super-secret-token",
    )
    assert search.status_code == 200
    search_content = search.json()["result"]["structuredContent"]
    assert search_content["search_mode"] == "keyword_fallback"
    assert len(search_content["items"]) >= 1


def test_mcp_not_found_error_surfaces_as_tool_error(client: TestClient):
    _reset_data()
    missing_id = str(uuid.uuid4())
    response = _mcp_call(
        client,
        request_id=9,
        method="tools/call",
        params={"name": "list_documentation_sections", "arguments": {"documentation_id": missing_id}},
        token="super-secret-token",
    )

    assert response.status_code == 200
    payload = response.json()["result"]
    assert payload["isError"] is True
    assert "Documentation not found" in payload["content"][0]["text"]
