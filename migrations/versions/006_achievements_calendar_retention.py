"""Achievements, calendar, retention.

Revision ID: 006
Revises: 005
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.String(256), nullable=False),
        sa.Column("icon", sa.String(10), nullable=False, server_default="🏆"),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("condition_type", sa.String(32), nullable=False),
        sa.Column("condition_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_achievements_code", "achievements", ["code"], unique=True)

    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("ix_user_achievements_user_id", "user_achievements", ["user_id"])
    op.create_index("ix_user_achievements_achievement_id", "user_achievements", ["achievement_id"])

    op.add_column(
        "users",
        sa.Column("profile_views_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("last_paywall_shown_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Seed achievements
    op.execute(sa.text("""
        INSERT INTO achievements (code, title, description, icon, is_premium, condition_type, condition_value)
        VALUES
        ('first_habit', 'Первый шаг', 'Ты создал свою первую привычку — отличное начало!', '🎯', false, 'created_habits', 1),
        ('streak_3', 'Серия 3 дня', 'Три дня подряд — ты в ритме!', '🔥', false, 'streak', 3),
        ('streak_7', 'Серия 7 дней', 'Неделя без перерывов — это серьёзно!', '🔥', false, 'streak', 7),
        ('completed_10', '10 выполнений', 'Десять привычек выполнено — рост налицо!', '✅', false, 'completed_habits', 10),
        ('no_skips_7', 'Неделя без пропусков', 'Целую неделю без пропусков — дисциплина!', '📅', false, 'no_skips_7_days', 1),
        ('master_100', 'Мастер привычек', '100 выполнений — ты мастер!', '🏆', true, 'completed_habits', 100)
    """))


def downgrade() -> None:
    op.drop_column("users", "last_paywall_shown_at")
    op.drop_column("users", "profile_views_count")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
