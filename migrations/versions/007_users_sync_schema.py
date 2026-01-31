"""Sync users table with model — add missing columns (idempotent).

Revision ID: 007
Revises: 006
Create Date: 2025-01-31

Production-safe: uses IF NOT EXISTS for PostgreSQL.
Run after 006 or on DB that missed 004–006.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    """Check if column exists in table."""
    result = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
            """
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    """Add missing user columns — idempotent, safe for production."""
    conn = op.get_bind()

    columns_to_add = [
        ("last_inactivity_reminder_at", sa.Column("last_inactivity_reminder_at", sa.DateTime(timezone=True), nullable=True)),
        ("last_streak_milestone", sa.Column("last_streak_milestone", sa.Integer(), nullable=True)),
        ("notifications_enabled", sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true())),
        ("last_profile_quote_index", sa.Column("last_profile_quote_index", sa.Integer(), nullable=True)),
        ("last_insight_at", sa.Column("last_insight_at", sa.DateTime(timezone=True), nullable=True)),
        ("last_insight_id", sa.Column("last_insight_id", sa.Integer(), nullable=True)),
        ("profile_views_count", sa.Column("profile_views_count", sa.Integer(), nullable=False, server_default="0")),
        ("last_paywall_shown_at", sa.Column("last_paywall_shown_at", sa.DateTime(timezone=True), nullable=True)),
    ]

    for col_name, col_def in columns_to_add:
        if not _column_exists(conn, "users", col_name):
            op.add_column("users", col_def)


def downgrade() -> None:
    """Remove columns added by this migration (optional)."""
    # Downgrade intentionally no-op: columns may be used by app.
    # To fully revert, run migrations 006->001 downgrade.
    pass
