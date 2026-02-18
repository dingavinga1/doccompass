"""create ingestion phase tables

Revision ID: 20260218_000001
Revises:
Create Date: 2026-02-18 00:00:01
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20260218_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documentation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("last_synced", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cron_schedule", sa.String(length=255), nullable=True),
        sa.Column("crawl_depth", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("include_patterns", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("exclude_patterns", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )

    op.create_table(
        "documentation_section",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("documentation_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["documentation_id"], ["documentation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["documentation_section.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("documentation_id", "path", name="uq_documentation_section_doc_path"),
    )
    op.create_index("ix_documentation_section_documentation_id", "documentation_section", ["documentation_id"])
    op.create_index("ix_documentation_section_doc_path", "documentation_section", ["documentation_id", "path"])

    op.create_table(
        "ingestion_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("documentation_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stop_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["documentation_id"], ["documentation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_job_documentation_id", "ingestion_job", ["documentation_id"])

    op.create_table(
        "raw_page",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("documentation_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("markdown_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["documentation_id"], ["documentation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_page_documentation_id", "raw_page", ["documentation_id"])


def downgrade() -> None:
    op.drop_index("ix_raw_page_documentation_id", table_name="raw_page")
    op.drop_table("raw_page")

    op.drop_index("ix_ingestion_job_documentation_id", table_name="ingestion_job")
    op.drop_table("ingestion_job")

    op.drop_index("ix_documentation_section_doc_path", table_name="documentation_section")
    op.drop_index("ix_documentation_section_documentation_id", table_name="documentation_section")
    op.drop_table("documentation_section")

    op.drop_table("documentation")
