"""Full rebuild — habit_times, referrals, premium_until, premium_reward_days.

Revision ID: 012
Revises: 011
Create Date: 2025-01-31

Adds:
- users: premium_until, premium_reward_days (migrate from subscription_until)
- habit_times table
- referrals table
"""

from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: premium_until (from subscription_until if exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='subscription_until')
            AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='premium_until')
            THEN
                ALTER TABLE users RENAME COLUMN subscription_until TO premium_until;
            ELSIF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='premium_until')
            THEN
                ALTER TABLE users ADD COLUMN premium_until TIMESTAMP WITH TIME ZONE NULL;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='premium_reward_days')
            THEN
                ALTER TABLE users ADD COLUMN premium_reward_days INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;
    """)

    # habit_times
    op.execute("""
        CREATE TABLE IF NOT EXISTS habit_times (
            id SERIAL PRIMARY KEY,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            weekday INTEGER NOT NULL,
            time VARCHAR(5) NOT NULL,
            UNIQUE(habit_id, weekday, time)
        )
    """)

    # Migrate existing habits.remind_time -> habit_times (weekday 0 = Mon, all days)
    op.execute("""
        INSERT INTO habit_times (habit_id, weekday, time)
        SELECT id, 0, TO_CHAR(remind_time, 'HH24:MI')
        FROM habits
        WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='habits' AND column_name='remind_time')
        AND remind_time IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM habit_times WHERE habit_times.habit_id = habits.id)
    """)

    # Drop remind_time from habits
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='habits' AND column_name='remind_time')
            THEN
                ALTER TABLE habits DROP COLUMN remind_time;
            END IF;
        END $$;
    """)

    # referrals
    op.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            referral_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reward_given BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS referrals")
    op.execute("DROP TABLE IF EXISTS habit_times")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='premium_reward_days')
            THEN ALTER TABLE users DROP COLUMN premium_reward_days;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='premium_until')
            THEN ALTER TABLE users RENAME COLUMN premium_until TO subscription_until;
            END IF;
        END $$;
    """)
