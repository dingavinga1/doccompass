from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.api.dtos.common import ErrorResponse
from app.api.dtos.documentation import (
    DocumentationListResponse,
    PaginationMeta,
    DocumentationTreeResponse,
    SearchResponse,
    SectionContentResponse,
    SectionListResponse,
)
from app.db import get_session
from app.models import Documentation
from app.services.documentation import (
    build_search_items,
    delete_documentation,
    get_documentation_tree,
    get_section_content,
    list_documentations,
    list_sections,
    search_sections_keyword,
)

router = APIRouter(prefix="/documentation", tags=["documentation"])
ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.get("", response_model=DocumentationListResponse, responses=ERROR_RESPONSES)
def list_documentations_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> DocumentationListResponse:
    items, meta = list_documentations(session=session, limit=limit, offset=offset)
    return DocumentationListResponse(
        items=items,
        meta=PaginationMeta(total=meta.total, limit=meta.limit, offset=meta.offset),
    )


@router.get("/{documentation_id}", response_model=SectionListResponse, responses=ERROR_RESPONSES)
def list_documentation_sections_endpoint(
    documentation_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    start_path: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> SectionListResponse:
    documentation = session.get(Documentation, documentation_id)
    if documentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")

    items, meta = list_sections(
        session=session,
        documentation_id=documentation_id,
        limit=limit,
        offset=offset,
        start_path=start_path,
    )
    section_items = [
        {
            "id": section.id,
            "path": section.path,
            "title": section.title,
            "summary": section.summary,
            "level": section.level,
            "url": section.url,
            "token_count": section.token_count,
            "checksum": section.checksum,
        }
        for section in items
    ]
    return SectionListResponse(
        items=section_items,
        meta=PaginationMeta(total=meta.total, limit=meta.limit, offset=meta.offset),
    )


@router.get("/{documentation_id}/tree", response_model=DocumentationTreeResponse, responses=ERROR_RESPONSES)
def get_documentation_tree_endpoint(
    documentation_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> DocumentationTreeResponse:
    documentation = session.get(Documentation, documentation_id)
    if documentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")

    return DocumentationTreeResponse(
        documentation_id=documentation_id,
        roots=get_documentation_tree(session=session, documentation_id=documentation_id),
    )


@router.get("/{documentation_id}/search", response_model=SearchResponse, responses=ERROR_RESPONSES)
def search_documentation_endpoint(
    documentation_id: uuid.UUID,
    q: str = Query(min_length=2),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> SearchResponse:
    documentation = session.get(Documentation, documentation_id)
    if documentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")

    rows, meta = search_sections_keyword(
        session=session, documentation_id=documentation_id, query=q, limit=limit, offset=offset
    )
    return SearchResponse(
        items=build_search_items(rows, q),
        meta=PaginationMeta(total=meta.total, limit=meta.limit, offset=meta.offset),
    )


@router.get(
    "/{documentation_id}/sections/{section_path:path}",
    response_model=SectionContentResponse,
    responses=ERROR_RESPONSES,
)
def get_section_content_endpoint(
    documentation_id: uuid.UUID,
    section_path: str,
    session: Session = Depends(get_session),
) -> SectionContentResponse:
    documentation = session.get(Documentation, documentation_id)
    if documentation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")

    section = get_section_content(session=session, documentation_id=documentation_id, section_path=section_path)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return SectionContentResponse(
        id=section.id,
        documentation_id=section.documentation_id,
        path=section.path,
        parent_id=section.parent_id,
        title=section.title,
        summary=section.summary,
        content=section.content,
        level=section.level,
        url=section.url,
        token_count=section.token_count,
        checksum=section.checksum,
    )


@router.delete("/{documentation_id}", status_code=status.HTTP_204_NO_CONTENT, responses=ERROR_RESPONSES)
def delete_documentation_endpoint(
    documentation_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> Response:
    deleted = delete_documentation(session=session, documentation_id=documentation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
