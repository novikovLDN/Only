"""Add scheduler and analytics indexes — production validation.

Revision ID: 015
Revises: 014
Create Date: 2025-01-31

- idx_habit_times_lookup: scheduler weekday+time lookups
- idx_habit_logs_habit_id: habit analytics
"""

from typing import Sequence, Union

from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_habit_times_lookup ON habit_times(weekday, time)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id ON habit_logs(habit_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_habit_times_lookup")
    op.execute("DROP INDEX IF EXISTS idx_habit_logs_habit_id")
