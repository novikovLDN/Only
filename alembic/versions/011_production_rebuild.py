"""Production rebuild — clean schema aligned with app.models.

Revision ID: 011
Revises: 010
Create Date: 2025-01-31

Schema:
- users: id, telegram_id, username, first_name, language_code, timezone, subscription_until, created_at, updated_at
- habits: id, user_id, title, remind_time, is_active, created_at
- habit_logs: id, habit_id, user_id, date, status, skip_reason
- payments: id, user_id, telegram_payment_charge_id, provider_payment_charge_id, amount, created_at
- motivation_usage: id, user_id, phrase_index, used_at
"""

from typing import Sequence, Union

from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename users.language -> language_code if exists (010 had renamed language_code->language)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='language')
            AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='language_code')
            THEN
                ALTER TABLE users RENAME COLUMN language TO language_code;
            END IF;
        END $$;
    """)

    # Create motivation_usage if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS motivation_usage (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            phrase_index INTEGER NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS motivation_usage")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='language_code')
            THEN
                ALTER TABLE users RENAME COLUMN language_code TO language;
            END IF;
        END $$;
    """)
