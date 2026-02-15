"""Fix habit_logs.user_id — add column if missing (schema drift).

Revision ID: 009
Revises: 008
Create Date: 2025-01-31

Fixes: UndefinedColumnError when migration 008 creates index on user_id.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Ensure user_id column exists
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'habit_logs'
                  AND column_name = 'user_id'
            ) THEN
                ALTER TABLE habit_logs ADD COLUMN user_id BIGINT;
                -- Backfill from habits
                UPDATE habit_logs hl
                SET user_id = h.user_id
                FROM habits h
                WHERE hl.habit_id = h.id;
                -- Remove orphans (habit deleted) before NOT NULL
                DELETE FROM habit_logs WHERE user_id IS NULL;
                ALTER TABLE habit_logs ALTER COLUMN user_id SET NOT NULL;
            END IF;
        END $$;
    """)

    # 2) Add FK if missing
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'habit_logs'::regclass
                  AND conname = 'habit_logs_user_id_fkey'
            ) THEN
                ALTER TABLE habit_logs
                ADD CONSTRAINT habit_logs_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)

    # 4) Ensure created_at exists (008 may have failed before it)
    op.execute("ALTER TABLE habit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

    # 5) Create indexes safely
    op.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_user_id ON habit_logs(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id ON habit_logs(habit_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_habit_logs_created_at ON habit_logs(created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_habit_logs_created_at")
    op.execute("DROP INDEX IF EXISTS idx_habit_logs_habit_id")
    op.execute("DROP INDEX IF EXISTS idx_habit_logs_user_id")
    # Do not drop user_id — may have data; downgrade is no-op for column
