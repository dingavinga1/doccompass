from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models import IngestionStatus


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class DocumentationSummary(BaseModel):
    id: uuid.UUID
    url: str
    title: str | None
    last_synced: datetime | None
    created_at: datetime
    updated_at: datetime
    section_count: int
    job_count: int
    last_job_status: IngestionStatus | None


class DocumentationListResponse(BaseModel):
    items: list[DocumentationSummary]
    meta: PaginationMeta


class SectionSummary(BaseModel):
    id: uuid.UUID
    path: str
    title: str | None
    summary: str | None
    level: int | None
    url: str | None
    token_count: int | None
    checksum: str | None


class SectionListResponse(BaseModel):
    items: list[SectionSummary]
    meta: PaginationMeta


class SectionContentResponse(BaseModel):
    id: uuid.UUID
    documentation_id: uuid.UUID
    path: str
    parent_id: uuid.UUID | None
    title: str | None
    summary: str | None
    content: str | None
    level: int | None
    url: str | None
    token_count: int | None
    checksum: str | None


class DocumentationTreeNode(BaseModel):
    id: uuid.UUID
    path: str
    parent_id: uuid.UUID | None
    title: str | None
    level: int | None
    children: list["DocumentationTreeNode"] = Field(default_factory=list)


class DocumentationTreeResponse(BaseModel):
    documentation_id: uuid.UUID
    roots: list[DocumentationTreeNode]


class SearchItem(BaseModel):
    id: uuid.UUID
    path: str
    title: str | None
    summary: str | None
    excerpt: str
    score: float


class SearchResponse(BaseModel):
    search_mode: Literal["keyword_fallback"] = "keyword_fallback"
    items: list[SearchItem]
    meta: PaginationMeta
