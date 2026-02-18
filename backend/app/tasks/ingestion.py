from __future__ import annotations

import asyncio
import uuid

from app.celery_app import celery_app
from app.db import engine
from app.services.ingestion import run_ingestion_pipeline
from sqlmodel import Session


@celery_app.task(name="app.tasks.ingestion.run_ingestion")
def run_ingestion(job_id: str) -> dict[str, str]:
    ingestion_job_id = uuid.UUID(job_id)

    with Session(engine) as session:
        asyncio.run(run_ingestion_pipeline(session, ingestion_job_id))

    return {"job_id": job_id}
