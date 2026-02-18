import asyncio
import uuid

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Documentation, DocumentationSection, IngestionJob, IngestionStatus
from app.services.crawler import CrawledPage
from app.services.ingestion import run_ingestion_pipeline
from app.services.parser import ParsedSection


def _make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_ingestion_pipeline_completes_and_upserts_delta(monkeypatch):
    session = _make_session()
    doc = Documentation(url="https://example.com", crawl_depth=2)
    session.add(doc)
    session.commit()
    session.refresh(doc)

    job = IngestionJob(documentation_id=doc.id)
    session.add(job)
    session.commit()
    session.refresh(job)

    async def fake_crawl_site(**kwargs):
        return [CrawledPage(url="https://example.com", markdown="# Home\nText", html=None, depth=0)]

    def fake_parse_sections(pages):
        return [
            ParsedSection(
                path="/example/home",
                parent_path=None,
                title="Home",
                summary="Text",
                content="Text",
                level=1,
                url="https://example.com",
                token_count=1,
                checksum="abc123",
            )
        ]

    monkeypatch.setattr("app.services.ingestion.crawl_site", fake_crawl_site)
    monkeypatch.setattr("app.services.ingestion.parse_sections", fake_parse_sections)

    asyncio.run(run_ingestion_pipeline(session, job.id))
    first_sections = session.exec(select(DocumentationSection)).all()

    asyncio.run(run_ingestion_pipeline(session, job.id))
    second_sections = session.exec(select(DocumentationSection)).all()

    refreshed_job = session.get(IngestionJob, job.id)
    assert refreshed_job is not None
    assert refreshed_job.status == IngestionStatus.COMPLETED
    assert refreshed_job.progress_percent == 100
    assert len(first_sections) == 1
    assert len(second_sections) == 1


def test_ingestion_pipeline_marks_stopped_when_requested(monkeypatch):
    session = _make_session()
    doc = Documentation(url="https://example.com", crawl_depth=2)
    session.add(doc)
    session.commit()
    session.refresh(doc)

    job = IngestionJob(documentation_id=doc.id, stop_requested=True)
    session.add(job)
    session.commit()

    async def fake_crawl_site(**kwargs):
        raise AssertionError("crawl should not be called when stop is requested")

    monkeypatch.setattr("app.services.ingestion.crawl_site", fake_crawl_site)

    asyncio.run(run_ingestion_pipeline(session, job.id))

    refreshed_job = session.get(IngestionJob, job.id)
    assert refreshed_job is not None
    assert refreshed_job.status == IngestionStatus.STOPPED
