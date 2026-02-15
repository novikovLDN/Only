"""Referral hardening: is_active, invited_id UNIQUE.

Revision ID: 004
Revises: 003
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_referrals_invited_id'
            ) THEN
                ALTER TABLE referrals ADD CONSTRAINT uq_referrals_invited_id UNIQUE (invited_id);
            END IF;
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END
        $$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE referrals DROP CONSTRAINT IF EXISTS uq_referrals_invited_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_active")
