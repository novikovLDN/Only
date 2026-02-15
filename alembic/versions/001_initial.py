"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables already exist (created manually or by hotfix). Do not recreate.
    pass


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("referrals")
    op.drop_table("habit_times")
    op.drop_table("habit_days")
    op.drop_table("habits")
    op.drop_table("users")
