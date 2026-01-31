"""
RetentionService — inactivity reminders, streak rewards.

Проверка актуального статуса, не раздражать пользователя.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.user import User
from app.repositories.habit_repo import HabitRepository

logger = logging.getLogger(__name__)

INACTIVITY_DAYS = 3
INACTIVITY_REMINDER_COOLDOWN_DAYS = 7
STREAK_MILESTONES = (7, 14, 30, 60, 100)


class RetentionService:
    """Inactivity reminders, streak rewards."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._habit_repo = HabitRepository(session)

    async def get_users_for_inactivity_reminder(self) -> list[User]:
        """
        Users with habits but no completed log in INACTIVITY_DAYS.
        Respects last_inactivity_reminder_at cooldown.
        """
        from app.models.habit_log import HabitLog

        today = date.today()
        cutoff = today - timedelta(days=INACTIVITY_DAYS)
        cooldown_cutoff = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_REMINDER_COOLDOWN_DAYS)
        # Users with active habits who have no completed log since cutoff
        # and (no reminder sent or reminder older than cooldown)
        subq = (
            select(Habit.user_id)
            .where(Habit.is_active == True)
            .distinct()
        )
        result = await self._session.execute(
            select(User)
            .where(User.id.in_(subq))
            .where(User.is_blocked == False)
            .where(
                (User.last_inactivity_reminder_at.is_(None))
                | (User.last_inactivity_reminder_at < cooldown_cutoff)
            )
        )
        users = list(result.scalars().unique().all())
        out = []
        for user in users:
            last = await self._habit_repo.get_last_activity_date(user.id)
            if last is None or last < cutoff:
                out.append(user)
        return out

    async def mark_inactivity_reminder_sent(self, user: User) -> None:
        """Update last_inactivity_reminder_at."""
        user.last_inactivity_reminder_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def get_users_for_streak_milestone(self) -> list[tuple[User, int]]:
        """
        Users who hit a new streak milestone (7, 14, 30, 60, 100).
        Returns [(user, streak)].
        """
        from app.models.habit_log import HabitLog

        # Users with at least one completed habit
        subq = (
            select(Habit.user_id)
            .join(HabitLog, HabitLog.habit_id == Habit.id)
            .where(HabitLog.completed == True)
            .distinct()
        )
        result = await self._session.execute(
            select(User).where(User.id.in_(subq)).where(User.is_blocked == False)
        )
        users = list(result.scalars().unique().all())
        out = []
        for user in users:
            streak = await self._habit_repo.get_current_streak(user.id)
            last_milestone = user.last_streak_milestone or 0
            for m in STREAK_MILESTONES:
                if streak >= m and last_milestone < m:
                    out.append((user, m))
                    break
        return out

    async def mark_streak_milestone_sent(self, user: User, milestone: int) -> None:
        """Update last_streak_milestone."""
        user.last_streak_milestone = milestone
        await self._session.flush()
