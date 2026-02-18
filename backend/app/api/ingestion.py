from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.services.ingestion import get_ingestion_job, request_stop, start_ingestion
from app.api.dtos.ingestion import (
    IngestionStatusResponse,
    StartIngestionRequest,
    StartIngestionResponse,
    StopIngestionRequest,
    StopIngestionResponse,
)

router = APIRouter(prefix="/documentation", tags=["ingestion"])


@router.post("/ingestion", response_model=StartIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
def start_ingestion_endpoint(
    payload: StartIngestionRequest,
    session: Session = Depends(get_session),
) -> StartIngestionResponse:
    job = start_ingestion(
        session=session,
        web_url=payload.web_url,
        crawl_depth=payload.crawl_depth,
        include_patterns=payload.include_patterns,
        exclude_patterns=payload.exclude_patterns,
    )
    return StartIngestionResponse(job_id=job.id, documentation_id=job.documentation_id, status=job.status)


@router.get("/ingestion/{job_id}", response_model=IngestionStatusResponse)
def get_ingestion_status_endpoint(job_id: uuid.UUID, session: Session = Depends(get_session)) -> IngestionStatusResponse:
    job = get_ingestion_job(session, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")

    return IngestionStatusResponse(
        job_id=job.id,
        documentation_id=job.documentation_id,
        status=job.status,
        progress_percent=job.progress_percent,
        pages_processed=job.pages_processed,
        stop_requested=job.stop_requested,
        error_message=job.error_message,
    )


@router.post("/ingestion/stop", response_model=StopIngestionResponse)
def stop_ingestion_endpoint(
    payload: StopIngestionRequest,
    session: Session = Depends(get_session),
) -> StopIngestionResponse:
    job = request_stop(session, payload.job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")

    return StopIngestionResponse(job_id=job.id, status=job.status, stop_requested=job.stop_requested)
