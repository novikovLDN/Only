"""Fix schema mismatch — users.language_code→language, habits.name→title.

Revision ID: 010
Revises: 009
Create Date: 2025-01-31

Fixes:
- users: language_code NOT NULL but code uses language
- habits: name NOT NULL but code uses title
"""

from typing import Sequence, Union

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) users: if DB has language_code but not language — rename
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'language_code'
            )
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'language'
            ) THEN
                ALTER TABLE users RENAME COLUMN language_code TO language;
            END IF;
        END $$;
    """)
    # Ensure language NOT NULL with default (if column exists)
    op.execute("UPDATE users SET language = 'ru' WHERE language IS NULL")
    op.execute("ALTER TABLE users ALTER COLUMN language SET DEFAULT 'ru'")
    op.execute("ALTER TABLE users ALTER COLUMN language SET NOT NULL")

    # 2) habits: if DB has name but not title — rename
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'habits' AND column_name = 'name'
            )
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'habits' AND column_name = 'title'
            ) THEN
                ALTER TABLE habits RENAME COLUMN name TO title;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    pass
