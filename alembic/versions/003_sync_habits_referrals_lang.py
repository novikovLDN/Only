"""Sync habits, referrals schema; users.language nullable.

Revision ID: 003
Revises: 002
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE habits ADD COLUMN IF NOT EXISTS title VARCHAR(200) NOT NULL DEFAULT ''
    """)
    op.execute("""
        ALTER TABLE habits ADD COLUMN IF NOT EXISTS is_custom BOOLEAN NOT NULL DEFAULT true
    """)
    op.execute("""
        ALTER TABLE habits ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    """)
    op.execute("""
        ALTER TABLE referrals ADD COLUMN IF NOT EXISTS inviter_id BIGINT
    """)
    op.execute("""
        ALTER TABLE referrals ADD COLUMN IF NOT EXISTS invited_id BIGINT
    """)
    op.execute("""
        ALTER TABLE referrals ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    """)
    op.execute("""
        ALTER TABLE users ALTER COLUMN language DROP NOT NULL
    """)
    op.execute("""
        ALTER TABLE users ALTER COLUMN language SET DEFAULT NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN language SET DEFAULT 'en'")
    op.execute("ALTER TABLE users ALTER COLUMN language SET NOT NULL")