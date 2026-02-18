from collections.abc import Generator
import logging

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.postgres_connection_string, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def create_all() -> None:
    SQLModel.metadata.create_all(engine)


def db_healthcheck() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def pgvector_healthcheck() -> tuple[bool, str | None]:
    try:
        with engine.connect() as conn:
            installed = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            ).scalar()

        if bool(installed):
            return True, None

        message = "PGVector extension 'vector' is not installed in the target database."
        logger.warning(message)
        return False, message
    except Exception as exc:
        message = f"Unable to verify PGVector extension availability: {exc}"
        logger.exception("PGVector healthcheck failed")
        return False, message
