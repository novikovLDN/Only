"""User metrics table for achievements engine.

Revision ID: 018
Revises: 017
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_metrics",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_no_misses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("perfect_days_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_completions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completions_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completions_last_7_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completions_last_30_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("perfect_days_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("perfect_weeks_in_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("all_habits_completed_today", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("all_habits_completed_7_days", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("returned_after_miss_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("habits_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("habit_modified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("streak_preserved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("habit_goal_increased", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("new_habit_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("habits_completed_daily", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invited_friends", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("friends_with_7_day_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sync_with_friend_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_friends_30_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_categories", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("subscription_months", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_metrics")
