"""Progress service — daily status, recalculation, missed habits."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import DailyProgress, HabitLog
from app.repositories.daily_progress_repo import DailyProgressRepository
from app.repositories.habit_log_repo import HabitLogRepository
from app.repositories.habit_repo import HabitRepository


class ProgressService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.daily_repo = DailyProgressRepository(session)
        self.habit_log_repo = HabitLogRepository(session)
        self.habit_repo = HabitRepository(session)

    async def recalc_daily_for_user(self, user_id: int, d: date) -> None:
        """If all habits completed → success; if any declined → missed."""
        habits = await self.habit_repo.get_user_habits(user_id)
        if not habits:
            return
        target_weekday = d.weekday()
        active_habits = [h for h in habits if any(hd.weekday == target_weekday for hd in h.days)]
        if not active_habits:
            return
        success = True
        for habit in active_habits:
            log = await self.habit_log_repo.get_by_user_habit_date(user_id, habit.id, d)
            if log is None:
                success = False
                break
            if log.status == "declined" or log.status == "missed":
                success = False
                break
        await self.daily_repo.upsert(user_id, d, success)

    async def get_month_progress(self, user_id: int, year: int, month: int) -> tuple[int, int, list[tuple[date, bool | None]]]:
        """Returns (success_count, total_days, [(date, success|None), ...]). Uses daily_progress; None = no data."""
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        result = await self.session.execute(
            select(DailyProgress).where(
                DailyProgress.user_id == user_id,
                DailyProgress.date >= start,
                DailyProgress.date <= end,
            )
        )
        rows = result.scalars().all()
        success_count = sum(1 for r in rows if r.success)
        total = (end - start).days + 1
        by_date = {r.date: r.success for r in rows}
        days_list = [(start + timedelta(days=i), by_date.get(start + timedelta(days=i))) for i in range(total)]
        return success_count, total, days_list

    async def get_missed_habits(self, user_id: int, year: int, month: int) -> list[tuple[date, str, str]]:
        """Returns [(date, habit_title, reason), ...] for declined habits in month."""
        from app.core.models import Habit

        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        result = await self.session.execute(
            select(HabitLog, Habit)
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(
                HabitLog.user_id == user_id,
                HabitLog.status == "declined",
                HabitLog.date >= start,
                HabitLog.date <= end,
            )
            .order_by(HabitLog.date.desc())
        )
        return [(log.date, habit.title, log.reason or "") for log, habit in result.all()]
