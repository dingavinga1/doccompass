from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api import documentation_router, ingestion_router
from .config import settings
from .db import db_healthcheck, pgvector_healthcheck
from .mcp import mount_mcp_server
from .redis_client import redis_healthcheck

def create_app() -> FastAPI:
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

    @app.get("/ready")
    def readiness() -> JSONResponse:
        db_ok = db_healthcheck()
        redis_ok = redis_healthcheck()
        pgvector_ok, pgvector_message = pgvector_healthcheck()
        is_ready = db_ok and redis_ok and pgvector_ok
        payload: dict[str, object] = {
            "status": "ok" if is_ready else "degraded",
            "services": {
                "database": "ok" if db_ok else "down",
                "redis": "ok" if redis_ok else "down",
                "pgvector": "ok" if pgvector_ok else "down",
            },
        }
        if pgvector_message:
            payload["details"] = {"pgvector": pgvector_message}

        status_code = 200 if is_ready else 503
        return JSONResponse(status_code=status_code, content=payload)

    mount_mcp_server(app)

    return app


app = create_app()
