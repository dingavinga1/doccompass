from sqlalchemy import text
from sqlmodel import create_engine

from .config import settings


engine = create_engine(settings.postgres_connection_string, pool_pre_ping=True)


def db_healthcheck() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
