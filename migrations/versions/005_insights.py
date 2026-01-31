"""Insights fields for profile.

Revision ID: 005
Revises: 004
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_insight_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_insight_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_insight_id")
    op.drop_column("users", "last_insight_at")
