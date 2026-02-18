from __future__ import annotations

import uuid

from fastapi import status
from pydantic import BaseModel, Field

from app.models import IngestionStatus


class StartIngestionRequest(BaseModel):
    web_url: str = Field(min_length=1)
    crawl_depth: int = Field(default=3, ge=0, le=10)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)


class StartIngestionResponse(BaseModel):
    job_id: uuid.UUID
    documentation_id: uuid.UUID
    status: IngestionStatus


class IngestionStatusResponse(BaseModel):
    job_id: uuid.UUID
    documentation_id: uuid.UUID
    status: IngestionStatus
    progress_percent: int
    pages_processed: int
    stop_requested: bool
    error_message: str | None


class StopIngestionRequest(BaseModel):
    job_id: uuid.UUID


class StopIngestionResponse(BaseModel):
    job_id: uuid.UUID
    status: IngestionStatus
    stop_requested: bool
