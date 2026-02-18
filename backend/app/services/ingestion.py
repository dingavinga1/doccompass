from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, delete, select

from app.celery_app import celery_app
from app.config import settings
from app.models import Documentation, DocumentationSection, IngestionJob, IngestionStatus, RawPage
from app.services.crawler import crawl_site
from app.services.parser import ParsedSection, parse_sections


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def start_ingestion(
    session: Session,
    web_url: str,
    crawl_depth: int = 3,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> IngestionJob:
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    doc = session.exec(select(Documentation).where(Documentation.url == web_url)).first()
    if doc is None:
        doc = Documentation(
            url=web_url,
            crawl_depth=crawl_depth,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        session.add(doc)
        session.flush()
    else:
        doc.crawl_depth = crawl_depth
        doc.include_patterns = include_patterns
        doc.exclude_patterns = exclude_patterns

    job = IngestionJob(
        documentation_id=doc.id,
        status=IngestionStatus.PENDING,
        progress_percent=0,
        pages_processed=0,
        stop_requested=False,
        error_message=None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    celery_app.send_task("app.tasks.ingestion.run_ingestion", args=[str(job.id)])
    return job


def get_ingestion_job(session: Session, job_id: uuid.UUID) -> IngestionJob | None:
    return session.get(IngestionJob, job_id)


def request_stop(session: Session, job_id: uuid.UUID) -> IngestionJob | None:
    job = session.get(IngestionJob, job_id)
    if job is None:
        return None

    if job.status in {IngestionStatus.COMPLETED, IngestionStatus.FAILED, IngestionStatus.STOPPED}:
        return job

    job.stop_requested = True
    job.updated_at = _utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _set_job_state(
    session: Session,
    job: IngestionJob,
    status: IngestionStatus,
    progress_percent: int | None = None,
    pages_processed: int | None = None,
    error_message: str | None = None,
) -> IngestionJob:
    job.status = status
    if progress_percent is not None:
        job.progress_percent = progress_percent
    if pages_processed is not None:
        job.pages_processed = pages_processed
    if error_message is not None:
        job.error_message = error_message
    job.updated_at = _utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _stop_if_requested(session: Session, job: IngestionJob) -> bool:
    refreshed = session.get(IngestionJob, job.id)
    if refreshed is None:
        return True
    if refreshed.stop_requested:
        _set_job_state(session, refreshed, IngestionStatus.STOPPED, error_message=None)
        return True
    return False


def _persist_raw_pages(session: Session, documentation_id: uuid.UUID, pages: list) -> None:
    if not settings.store_raw_pages:
        return

    session.exec(delete(RawPage).where(RawPage.documentation_id == documentation_id))
    for page in pages:
        session.add(
            RawPage(
                documentation_id=documentation_id,
                url=page.url,
                html_content=page.html,
                markdown_content=page.markdown,
            )
        )
    session.commit()


def _apply_sections_delta(session: Session, documentation_id: uuid.UUID, parsed_sections: list[ParsedSection]) -> None:
    existing_sections = session.exec(
        select(DocumentationSection).where(DocumentationSection.documentation_id == documentation_id)
    ).all()
    existing_by_path = {section.path: section for section in existing_sections}

    incoming_paths = {section.path for section in parsed_sections}
    path_to_model: dict[str, DocumentationSection] = {}

    for parsed in parsed_sections:
        existing = existing_by_path.get(parsed.path)
        if existing and existing.checksum == parsed.checksum:
            path_to_model[parsed.path] = existing
            continue

        if existing is None:
            existing = DocumentationSection(documentation_id=documentation_id, path=parsed.path)

        existing.title = parsed.title
        existing.summary = parsed.summary
        existing.content = parsed.content
        existing.level = parsed.level
        existing.url = parsed.url
        existing.token_count = parsed.token_count
        existing.checksum = parsed.checksum
        existing.updated_at = _utcnow()

        session.add(existing)
        session.flush()
        path_to_model[parsed.path] = existing

    stale_sections = [section for section in existing_sections if section.path not in incoming_paths]
    for stale in stale_sections:
        session.delete(stale)

    session.flush()

    for parsed in parsed_sections:
        target = path_to_model.get(parsed.path)
        if target is None:
            continue
        if parsed.parent_path is None:
            target.parent_id = None
            continue
        parent = path_to_model.get(parsed.parent_path)
        target.parent_id = parent.id if parent else None

    session.commit()


async def run_ingestion_pipeline(session: Session, job_id: uuid.UUID) -> None:
    job = session.get(IngestionJob, job_id)
    if job is None:
        return

    documentation = session.get(Documentation, job.documentation_id)
    if documentation is None:
        _set_job_state(session, job, IngestionStatus.FAILED, error_message="Missing documentation row")
        return

    try:
        if _stop_if_requested(session, job):
            return

        _set_job_state(session, job, IngestionStatus.CRAWLING, progress_percent=10)
        pages = await crawl_site(
            start_url=documentation.url,
            max_depth=documentation.crawl_depth,
            include_patterns=documentation.include_patterns,
            exclude_patterns=documentation.exclude_patterns,
        )
        _set_job_state(session, job, IngestionStatus.CRAWLING, progress_percent=40, pages_processed=len(pages))
        _persist_raw_pages(session, documentation.id, pages)

        if _stop_if_requested(session, job):
            return

        _set_job_state(session, job, IngestionStatus.PARSING, progress_percent=55, pages_processed=len(pages))
        parsed_sections = parse_sections(pages)
        _apply_sections_delta(session, documentation.id, parsed_sections)

        if _stop_if_requested(session, job):
            return

        _set_job_state(session, job, IngestionStatus.EMBEDDING, progress_percent=80)
        # Embedding intentionally stubbed for this phase.

        if _stop_if_requested(session, job):
            return

        _set_job_state(session, job, IngestionStatus.INDEXING, progress_percent=95)
        # Indexing intentionally stubbed for this phase.

        documentation.last_synced = _utcnow()
        documentation.updated_at = _utcnow()
        session.add(documentation)
        session.commit()

        _set_job_state(session, job, IngestionStatus.COMPLETED, progress_percent=100, error_message=None)
    except Exception as exc:
        _set_job_state(session, job, IngestionStatus.FAILED, error_message=str(exc))
