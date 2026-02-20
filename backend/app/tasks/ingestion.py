from __future__ import annotations

import asyncio
import logging
import uuid

from app.celery_app import celery_app
from app.db import engine
from app.services.ingestion import run_ingestion_pipeline
from sqlmodel import Session

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.ingestion.run_ingestion")
def run_ingestion(job_id: str) -> dict[str, str]:
    ingestion_job_id = uuid.UUID(job_id)

    try:
        with Session(engine) as session:
            asyncio.run(run_ingestion_pipeline(session, ingestion_job_id))
    except BaseException as exc:
        # Safety net: if the pipeline's own handler missed the error,
        # force the job into FAILED state so it doesn't stay stuck.
        logger.exception("Ingestion task %s crashed: %s", job_id, exc)
        try:
            from app.models import IngestionJob, IngestionStatus

            with Session(engine) as fallback_session:
                job = fallback_session.get(IngestionJob, ingestion_job_id)
                if job and job.status not in (
                    IngestionStatus.COMPLETED,
                    IngestionStatus.FAILED,
                    IngestionStatus.STOPPED,
                ):
                    job.status = IngestionStatus.FAILED
                    job.error_message = f"Unhandled error: {exc}"
                    fallback_session.add(job)
                    fallback_session.commit()
        except Exception:
            logger.exception("Failed to mark job %s as FAILED in safety net", job_id)

    return {"job_id": job_id}
