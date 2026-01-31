"""Profile and settings fields.

Revision ID: 004
Revises: 003
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("last_profile_quote_index", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_profile_quote_index")
    op.drop_column("users", "notifications_enabled")
