from fastapi import FastAPI

from .api import documentation_router, ingestion_router
from .config import settings
from .db import db_healthcheck
from .redis_client import redis_healthcheck

app = FastAPI(title=settings.app_name)
app.include_router(ingestion_router)
app.include_router(documentation_router)


@app.get("/health")
def health() -> dict[str, object]:
    db_ok = db_healthcheck()
    redis_ok = redis_healthcheck()
    overall = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "services": {
            "database": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "down",
        },
    }
