"""
Habit repository.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.habit_schedule import HabitSchedule
from app.repositories.base import BaseRepository


class HabitRepository(BaseRepository[Habit]):
    """Habit data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Habit)

    async def get_user_habits(self, user_id: int, active_only: bool = True) -> list[Habit]:
        """Get all habits for user."""
        q = select(Habit).where(Habit.user_id == user_id)
        if active_only:
            q = q.where(Habit.is_active == True)
        q = q.options(selectinload(Habit.schedules)).order_by(Habit.created_at.desc())
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count_user_habits(self, user_id: int) -> int:
        """Count active habits for user."""
        result = await self._session.execute(
            select(func.count(Habit.id)).where(
                and_(Habit.user_id == user_id, Habit.is_active == True)
            )
        )
        return result.scalar() or 0

    async def get_with_schedules(self, habit_id: int, user_id: int) -> Habit | None:
        """Get habit by ID with schedules, ensuring user ownership."""
        result = await self._session.execute(
            select(Habit)
            .where(and_(Habit.id == habit_id, Habit.user_id == user_id))
            .options(selectinload(Habit.schedules))
        )
        return result.scalar_one_or_none()

    async def get_habit_log(
        self, habit_id: int, log_date: date
    ) -> HabitLog | None:
        """Get log for habit on date."""
        result = await self._session.execute(
            select(HabitLog).where(
                and_(HabitLog.habit_id == habit_id, HabitLog.log_date == log_date)
            )
        )
        return result.scalar_one_or_none()

    async def get_last_activity_date(self, user_id: int) -> date | None:
        """Last date user completed at least one habit."""
        result = await self._session.execute(
            select(func.max(HabitLog.log_date))
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(
                and_(
                    Habit.user_id == user_id,
                    HabitLog.completed == True,
                )
            )
        )
        return result.scalar()

    async def get_current_streak(self, user_id: int, until_date: date | None = None) -> int:
        """
        Consecutive days with at least one completed habit, counting backwards from until_date.
        Streak = number of consecutive days (including until_date) with activity.
        """
        from sqlalchemy import distinct

        end = until_date or date.today()
        # Get distinct dates user completed any habit, ordered desc
        result = await self._session.execute(
            select(distinct(HabitLog.log_date))
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(
                and_(
                    Habit.user_id == user_id,
                    HabitLog.completed == True,
                    HabitLog.log_date <= end,
                )
            )
            .order_by(HabitLog.log_date.desc())
            .limit(500)
        )
        activity_dates = {r[0] for r in result.fetchall()}
        streak = 0
        cursor = end
        while cursor in activity_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak
