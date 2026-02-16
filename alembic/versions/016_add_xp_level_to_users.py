"""Add xp and level to users.

Revision ID: 016
Revises: 015
Create Date: 2025-01-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("xp", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("level", sa.Integer(), server_default="1", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "level")
    op.drop_column("users", "xp")
