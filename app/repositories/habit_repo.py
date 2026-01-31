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

    async def count_user_completed_logs(self, user_id: int) -> int:
        """Count completed habit logs for user (all time)."""
        result = await self._session.execute(
            select(func.count(HabitLog.id))
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(and_(Habit.user_id == user_id, HabitLog.completed == True))
        )
        return result.scalar() or 0

    async def count_user_skipped_logs(self, user_id: int) -> int:
        """Count skipped habit logs for user (all time)."""
        result = await self._session.execute(
            select(func.count(HabitLog.id))
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(and_(Habit.user_id == user_id, HabitLog.completed == False))
        )
        return result.scalar() or 0

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

    async def get_user_logs_per_day(
        self, user_id: int, from_date: date, to_date: date
    ) -> list[tuple[date, int, int]]:
        """Get per-day (completed_count, skipped_count) for user in date range. Returns [(date, completed, skipped), ...]."""
        from sqlalchemy import case

        result = await self._session.execute(
            select(
                HabitLog.log_date,
                func.sum(case((HabitLog.completed == True, 1), else_=0)),
                func.sum(case((HabitLog.completed == False, 1), else_=0)),
            )
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(
                and_(
                    Habit.user_id == user_id,
                    HabitLog.log_date >= from_date,
                    HabitLog.log_date <= to_date,
                )
            )
            .group_by(HabitLog.log_date)
        )
        rows = result.all()
        return [(r[0], int(r[1] or 0), int(r[2] or 0)) for r in rows]

    async def has_no_skips_last_n_days(self, user_id: int, days: int = 7) -> bool:
        """True if user had no skipped habits in the last N days (including today)."""
        today = date.today()
        from_date = today - timedelta(days=days - 1)
        logs = await self.get_user_logs_per_day(user_id, from_date, today)
        return not any(skipped > 0 for _, _, skipped in logs)

    async def has_no_skips_last_7_days(self, user_id: int, until_date: date | None = None) -> bool:
        """True if user had no skipped habits in the last 7 days."""
        end = until_date or date.today()
        start = end - timedelta(days=6)
        result = await self._session.execute(
            select(func.count(HabitLog.id))
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(
                and_(
                    Habit.user_id == user_id,
                    HabitLog.completed == False,
                    HabitLog.log_date >= start,
                    HabitLog.log_date <= end,
                )
            )
        )
        return (result.scalar() or 0) == 0

    async def get_day_calendar_status(
        self, user_id: int, d: date
    ) -> str:
        """
        For calendar: 'all' = all done, 'partial' = has skips, 'none' = no habits due.
        User must have had habits scheduled for that day (weekday match).
        """
        habits = await self.get_user_habits(user_id)
        due_habits = []
        for h in habits:
            for s in h.schedules:
                dow = s.days_of_week or "0,1,2,3,4,5,6"
                days = [int(x.strip()) for x in dow.split(",") if x.strip()]
                if d.weekday() in days:
                    due_habits.append(h)
                    break
        if not due_habits:
            return "none"
        completed = 0
        skipped = 0
        for h in due_habits:
            log = await self.get_habit_log(h.id, d)
            if log:
                if log.completed:
                    completed += 1
                else:
                    skipped += 1
        if skipped > 0:
            return "partial"
        if completed >= len(due_habits):
            return "all"
        return "partial"

    async def get_day_habit_logs(self, user_id: int, d: date) -> list[tuple[str, bool]]:
        """For day detail: [(habit_name, completed), ...] for habits due that day."""
        habits = await self.get_user_habits(user_id)
        result = []
        for h in habits:
            for s in h.schedules:
                dow = s.days_of_week or "0,1,2,3,4,5,6"
                days = [int(x.strip()) for x in dow.split(",") if x.strip()]
                if d.weekday() in days:
                    log = await self.get_habit_log(h.id, d)
                    completed = log.completed if log else False
                    result.append((f"{h.emoji or '📌'} {h.name}", completed))
                    break
        return result

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
