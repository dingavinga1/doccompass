from __future__ import annotations

import uuid
from dataclasses import dataclass
from urllib.parse import unquote

from sqlalchemy import case, desc, func, or_
from sqlmodel import Session, delete, select

from app.models import Documentation, DocumentationSection, IngestionJob, RawPage


@dataclass(slots=True)
class PaginationResult:
    total: int
    limit: int
    offset: int


def normalize_section_path(path: str) -> str:
    normalized = unquote(path).strip()
    if not normalized:
        return "/"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized


def list_documentations(session: Session, limit: int, offset: int) -> tuple[list[dict], PaginationResult]:
    total = session.exec(select(func.count()).select_from(Documentation)).one()
    docs = session.exec(select(Documentation).order_by(Documentation.created_at.desc()).offset(offset).limit(limit)).all()
    if not docs:
        return [], PaginationResult(total=total, limit=limit, offset=offset)

    doc_ids = [doc.id for doc in docs]

    section_counts = {
        doc_id: count
        for doc_id, count in session.exec(
            select(DocumentationSection.documentation_id, func.count(DocumentationSection.id))
            .where(DocumentationSection.documentation_id.in_(doc_ids))
            .group_by(DocumentationSection.documentation_id)
        ).all()
    }
    job_counts = {
        doc_id: count
        for doc_id, count in session.exec(
            select(IngestionJob.documentation_id, func.count(IngestionJob.id))
            .where(IngestionJob.documentation_id.in_(doc_ids))
            .group_by(IngestionJob.documentation_id)
        ).all()
    }

    latest_status: dict[uuid.UUID, str] = {}
    for job in session.exec(
        select(IngestionJob)
        .where(IngestionJob.documentation_id.in_(doc_ids))
        .order_by(IngestionJob.documentation_id, IngestionJob.created_at.desc())
    ).all():
        if job.documentation_id not in latest_status:
            latest_status[job.documentation_id] = job.status

    items = [
        {
            "id": doc.id,
            "url": doc.url,
            "title": doc.title,
            "last_synced": doc.last_synced,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "section_count": section_counts.get(doc.id, 0),
            "job_count": job_counts.get(doc.id, 0),
            "last_job_status": latest_status.get(doc.id),
        }
        for doc in docs
    ]
    return items, PaginationResult(total=total, limit=limit, offset=offset)


def list_sections(
    session: Session,
    documentation_id: uuid.UUID,
    limit: int,
    offset: int,
    start_path: str | None,
) -> tuple[list[DocumentationSection], PaginationResult]:
    base_query = select(DocumentationSection).where(DocumentationSection.documentation_id == documentation_id)
    count_query = select(func.count()).select_from(DocumentationSection).where(
        DocumentationSection.documentation_id == documentation_id
    )

    if start_path:
        normalized_start = normalize_section_path(start_path)
        like_pattern = f"{normalized_start}%"
        base_query = base_query.where(DocumentationSection.path.like(like_pattern))
        count_query = count_query.where(DocumentationSection.path.like(like_pattern))

    total = session.exec(count_query).one()
    sections = session.exec(base_query.order_by(DocumentationSection.path).offset(offset).limit(limit)).all()
    return sections, PaginationResult(total=total, limit=limit, offset=offset)


def get_section_content(
    session: Session, documentation_id: uuid.UUID, section_path: str
) -> DocumentationSection | None:
    normalized = normalize_section_path(section_path)
    return session.exec(
        select(DocumentationSection).where(
            DocumentationSection.documentation_id == documentation_id, DocumentationSection.path == normalized
        )
    ).first()


def get_documentation_tree(session: Session, documentation_id: uuid.UUID) -> list[dict]:
    sections = session.exec(
        select(DocumentationSection)
        .where(DocumentationSection.documentation_id == documentation_id)
        .order_by(DocumentationSection.path)
    ).all()

    nodes: dict[uuid.UUID, dict] = {}
    by_path: dict[str, dict] = {}
    roots: list[dict] = []

    for section in sections:
        node = {
            "id": section.id,
            "path": section.path,
            "parent_id": section.parent_id,
            "title": section.title,
            "level": section.level,
            "children": [],
        }
        nodes[section.id] = node
        by_path[section.path] = node

    for section in sections:
        node = nodes[section.id]
        parent_node = nodes.get(section.parent_id) if section.parent_id else None
        if parent_node is None and section.path.count("/") > 1:
            inferred_parent = section.path.rsplit("/", 1)[0]
            parent_node = by_path.get(inferred_parent)
        if parent_node is None:
            roots.append(node)
        else:
            parent_node["children"].append(node)

    def sort_nodes(items: list[dict]) -> None:
        items.sort(key=lambda n: n["path"])
        for item in items:
            sort_nodes(item["children"])

    sort_nodes(roots)
    return roots


def _make_excerpt(section: DocumentationSection, query: str) -> str:
    query_lower = query.lower()
    for value in [section.content or "", section.summary or "", section.title or ""]:
        idx = value.lower().find(query_lower)
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(value), idx + len(query) + 120)
            return value[start:end].strip()
    return (section.summary or section.content or section.title or "")[:160].strip()


def search_sections_keyword(
    session: Session,
    documentation_id: uuid.UUID,
    query: str,
    limit: int,
    offset: int,
) -> tuple[list[tuple[DocumentationSection, float]], PaginationResult]:
    pattern = f"%{query}%"
    predicates = or_(
        DocumentationSection.title.ilike(pattern),
        DocumentationSection.summary.ilike(pattern),
        DocumentationSection.content.ilike(pattern),
    )
    score_expr = (
        case((DocumentationSection.title.ilike(pattern), 3), else_=0)
        + case((DocumentationSection.summary.ilike(pattern), 2), else_=0)
        + case((DocumentationSection.content.ilike(pattern), 1), else_=0)
    ).label("score")

    total = session.exec(
        select(func.count())
        .select_from(DocumentationSection)
        .where(DocumentationSection.documentation_id == documentation_id, predicates)
    ).one()

    rows = session.exec(
        select(DocumentationSection, score_expr)
        .where(DocumentationSection.documentation_id == documentation_id, predicates)
        .order_by(desc("score"), DocumentationSection.path)
        .offset(offset)
        .limit(limit)
    ).all()

    results: list[tuple[DocumentationSection, float]] = []
    for section, score in rows:
        results.append((section, float(score)))

    return results, PaginationResult(total=total, limit=limit, offset=offset)


def delete_documentation(session: Session, documentation_id: uuid.UUID) -> bool:
    doc = session.get(Documentation, documentation_id)
    if doc is None:
        return False

    session.exec(delete(DocumentationSection).where(DocumentationSection.documentation_id == documentation_id))
    session.exec(delete(IngestionJob).where(IngestionJob.documentation_id == documentation_id))
    session.exec(delete(RawPage).where(RawPage.documentation_id == documentation_id))
    session.delete(doc)
    session.commit()
    return True


def build_search_items(rows: list[tuple[DocumentationSection, float]], query: str) -> list[dict]:
    return [
        {
            "id": section.id,
            "path": section.path,
            "title": section.title,
            "summary": section.summary,
            "excerpt": _make_excerpt(section, query),
            "score": score,
        }
        for section, score in rows
    ]
