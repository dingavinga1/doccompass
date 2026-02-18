import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import Column, DateTime, JSON, String, Text, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - fallback for environments without pgvector installed
    Vector = None

if Vector is not None:
    EMBEDDING_COLUMN_TYPE = JSON().with_variant(Vector(1536), "postgresql")
else:
    EMBEDDING_COLUMN_TYPE = JSON()


class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    CRAWLING = "CRAWLING"
    PARSING = "PARSING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Documentation(SQLModel, table=True):
    __tablename__ = "documentation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    url: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    title: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    last_synced: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    cron_schedule: str | None = Field(default=None, sa_column=Column(String(length=255), nullable=True))
    crawl_depth: int = Field(default=3, nullable=False)
    include_patterns: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False, server_default="[]"))
    exclude_patterns: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False, server_default="[]"))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )

    sections: list["DocumentationSection"] = Relationship(back_populates="documentation")
    jobs: list["IngestionJob"] = Relationship(back_populates="documentation")
    raw_pages: list["RawPage"] = Relationship(back_populates="documentation")


class DocumentationSection(SQLModel, table=True):
    __tablename__ = "documentation_section"
    __table_args__ = (UniqueConstraint("documentation_id", "path", name="uq_documentation_section_doc_path"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    documentation_id: uuid.UUID = Field(foreign_key="documentation.id", nullable=False, index=True)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="documentation_section.id")
    path: str = Field(sa_column=Column(Text, nullable=False))
    title: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    summary: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    level: int | None = Field(default=None, nullable=True)
    url: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    token_count: int | None = Field(default=None, nullable=True)
    checksum: str | None = Field(default=None, sa_column=Column(String(length=64), nullable=True))
    embedding: Any = Field(default=None, sa_column=Column(EMBEDDING_COLUMN_TYPE, nullable=True))

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )

    documentation: "Documentation" = Relationship(back_populates="sections")


class IngestionJob(SQLModel, table=True):
    __tablename__ = "ingestion_job"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    documentation_id: uuid.UUID = Field(foreign_key="documentation.id", nullable=False, index=True)
    status: IngestionStatus = Field(
        default=IngestionStatus.PENDING,
        sa_column=Column(String(length=32), nullable=False, default=IngestionStatus.PENDING.value),
    )
    error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    progress_percent: int = Field(default=0, nullable=False)
    pages_processed: int = Field(default=0, nullable=False)
    stop_requested: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )

    documentation: "Documentation" = Relationship(back_populates="jobs")


class RawPage(SQLModel, table=True):
    __tablename__ = "raw_page"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    documentation_id: uuid.UUID = Field(foreign_key="documentation.id", nullable=False, index=True)
    url: str = Field(sa_column=Column(Text, nullable=False))
    html_content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    markdown_content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )

    documentation: "Documentation" = Relationship(back_populates="raw_pages")
