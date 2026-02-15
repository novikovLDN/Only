"""Add missing columns to users.

Revision ID: 002
Revises: 001
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS language VARCHAR(5) NOT NULL DEFAULT 'ru'
    """)
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS subscription_until TIMESTAMPTZ
    """)
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS invited_by_id BIGINT
    """)
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) NOT NULL DEFAULT 'UTC'
    """)
    op.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_invited_by'
            ) THEN
                ALTER TABLE users
                ADD CONSTRAINT fk_users_invited_by
                FOREIGN KEY (invited_by_id) REFERENCES users(id) ON DELETE SET NULL;
            END IF;
        END
        $$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_invited_by")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS timezone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS invited_by_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS subscription_until")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS language")
