"""Hard reset — drop all tables, create fresh schema. No legacy migration.

Revision ID: 013
Revises: 012
Create Date: 2025-01-31

Production-safe: full clean rebuild.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop in order (respect FK dependencies)
    op.execute("DROP TABLE IF EXISTS motivation_usage CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_times CASCADE")
    op.execute("DROP TABLE IF EXISTS habits CASCADE")
    op.execute("DROP TABLE IF EXISTS referrals CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")

    # Fresh schema
    op.execute("""
        CREATE TABLE users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            language_code VARCHAR(5) NOT NULL DEFAULT 'ru',
            timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
            premium_until TIMESTAMP WITH TIME ZONE NULL,
            premium_reward_days INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NULL
        )
    """)

    op.execute("""
        CREATE TABLE habits (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE habit_times (
            id SERIAL PRIMARY KEY,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            weekday INTEGER NOT NULL,
            time VARCHAR(5) NOT NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX uniq_habit_time ON habit_times(habit_id, weekday, time)")

    op.execute("""
        CREATE TABLE habit_logs (
            id SERIAL PRIMARY KEY,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            status VARCHAR(20) NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            referral_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reward_given BOOLEAN DEFAULT FALSE
        )
    """)

    op.execute("""
        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            telegram_payment_charge_id VARCHAR(255),
            provider_payment_charge_id VARCHAR(255),
            amount INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE motivation_usage (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            phrase_index INTEGER NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS motivation_usage CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_times CASCADE")
    op.execute("DROP TABLE IF EXISTS habits CASCADE")
    op.execute("DROP TABLE IF EXISTS referrals CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
