"""users.language NOT NULL DEFAULT 'ru' and CHECK constraint.

Revision ID: 005
Revises: 004
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET language = 'ru' WHERE language IS NULL")
    op.execute("ALTER TABLE users ALTER COLUMN language SET DEFAULT 'ru'")
    op.execute("ALTER TABLE users ALTER COLUMN language SET NOT NULL")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'users_language_check'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_language_check
                CHECK (language IN ('ru', 'en'));
            END IF;
        END
        $$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_language_check")
    op.execute("ALTER TABLE users ALTER COLUMN language DROP NOT NULL")
    op.execute("ALTER TABLE users ALTER COLUMN language DROP DEFAULT")
