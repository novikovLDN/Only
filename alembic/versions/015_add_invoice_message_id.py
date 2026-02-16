"""Add invoice_message_id to payments.

Revision ID: 015
Revises: 014
Create Date: 2025-01-31

"""
from typing import Sequence, Union
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE payments ADD COLUMN IF NOT EXISTS invoice_message_id BIGINT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE payments DROP COLUMN IF EXISTS invoice_message_id")
