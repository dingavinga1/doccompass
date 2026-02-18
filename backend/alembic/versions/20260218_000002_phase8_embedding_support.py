"""phase8 embedding support

Revision ID: 20260218_000002
Revises: 20260218_000001
Create Date: 2026-02-18 16:50:00
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20260218_000002"
down_revision = "20260218_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change embedding column dimension from 1536 to 1024 (Titan v2 default)
    op.alter_column(
        "documentation_section",
        "embedding",
        type_=Vector(1024),
        existing_type=Vector(1536),
        existing_nullable=True,
    )

    # Add HNSW index for fast cosine similarity search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_documentation_section_embedding "
        "ON documentation_section USING hnsw (embedding vector_cosine_ops)"
    )

    # Add embedding metadata columns to documentation table
    op.add_column(
        "documentation",
        sa.Column("embedding_model_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "documentation",
        sa.Column("embedding_dimension_size", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documentation", "embedding_dimension_size")
    op.drop_column("documentation", "embedding_model_name")

    op.execute("DROP INDEX IF EXISTS ix_documentation_section_embedding")

    op.alter_column(
        "documentation_section",
        "embedding",
        type_=Vector(1536),
        existing_type=Vector(1024),
        existing_nullable=True,
    )
