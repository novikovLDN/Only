"""Add timezone index for scheduler performance.

Revision ID: 019
Revises: 018
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_timezone ON users (timezone)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_timezone")
