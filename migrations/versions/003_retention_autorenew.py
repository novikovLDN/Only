"""Retention and autorenew fields.

Revision ID: 003
Revises: 002
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("auto_renew_from_balance", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("last_renewal_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_inactivity_reminder_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_streak_milestone", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_streak_milestone")
    op.drop_column("users", "last_inactivity_reminder_at")
    op.drop_column("subscriptions", "last_renewal_attempt_at")
    op.drop_column("subscriptions", "auto_renew_from_balance")
