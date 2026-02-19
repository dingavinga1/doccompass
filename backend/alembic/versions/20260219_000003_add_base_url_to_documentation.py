"""add base_url to documentation

Revision ID: 20260219_000003
Revises: 20260218_000002
Create Date: 2026-02-19 08:33:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260219_000003"
down_revision = "20260218_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documentation",
        sa.Column("base_url", sa.Text(), nullable=True),
    )
    op.create_index("ix_documentation_base_url", "documentation", ["base_url"])


def downgrade() -> None:
    op.drop_index("ix_documentation_base_url", table_name="documentation")
    op.drop_column("documentation", "base_url")
