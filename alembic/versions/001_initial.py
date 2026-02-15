"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("subscription_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invited_by_id", sa.BigInteger(), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_foreign_key("fk_users_invited_by", "users", "users", ["invited_by_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "habit_days",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("habit_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["habit_id"], ["habits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "habit_times",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("habit_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(["habit_id"], ["habits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inviter_id", sa.BigInteger(), nullable=False),
        sa.Column("invited_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("tariff", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("referrals")
    op.drop_table("habit_times")
    op.drop_table("habit_days")
    op.drop_table("habits")
    op.drop_table("users")
