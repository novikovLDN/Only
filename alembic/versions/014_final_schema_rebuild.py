"""Final schema — production stable. FK consistency, TIME type, indexes.

Revision ID: 014
Revises: 013
Create Date: 2025-01-31

- All user FKs: BIGINT
- habit_times: TIME type, BIGINT habit_id, weekday SMALLINT
- habit_logs: log_date, created_at, index
- payments: YooKassa structure (tariff, provider, status)
- referrals: UNIQUE referral_user_id, created_at
- motivation_usage: habit_id for tracking
"""

from typing import Sequence, Union

from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop and recreate with final schema
    op.execute("DROP TABLE IF EXISTS motivation_usage CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS habit_times CASCADE")
    op.execute("DROP TABLE IF EXISTS habits CASCADE")
    op.execute("DROP TABLE IF EXISTS referrals CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")

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
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE habit_times (
            id BIGSERIAL PRIMARY KEY,
            habit_id BIGINT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            weekday SMALLINT NOT NULL,
            time TIME NOT NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX uniq_habit_time ON habit_times(habit_id, weekday, time)")

    op.execute("""
        CREATE TABLE habit_logs (
            id BIGSERIAL PRIMARY KEY,
            habit_id BIGINT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            log_date DATE NOT NULL,
            status VARCHAR(10) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_habit_logs_user_date ON habit_logs(user_id, log_date)")

    op.execute("""
        CREATE TABLE referrals (
            id BIGSERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            referral_user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reward_given BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE payments (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tariff VARCHAR(20) NOT NULL,
            amount INTEGER NOT NULL,
            provider VARCHAR(50) NOT NULL,
            external_payment_id VARCHAR(255),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_payments_user_id ON payments(user_id)")

    op.execute("""
        CREATE TABLE motivation_usage (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            habit_id BIGINT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
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
