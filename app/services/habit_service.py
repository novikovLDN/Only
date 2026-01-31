"""
Habit service — CRUD, logs, schedules.
"""

from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import HabitScheduleType
from app.models.habit_decline_note import HabitDeclineNote
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.habit_schedule import HabitSchedule
from app.repositories.habit_repo import HabitRepository
from app.utils.validators import validate_habit_name, validate_time


class HabitService:
    """Habit business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = HabitRepository(session)

    async def create_habit(
        self,
        user_id: int,
        name: str,
        description: str | None = None,
        emoji: str | None = None,
        schedule_type: str = HabitScheduleType.DAILY,
        reminder_time: str = "09:00",
        days_of_week: str | None = None,
        reminder_times: list[str] | None = None,
    ) -> Habit | None:
        """
        Create habit with schedule(s).
        If reminder_times provided — создаёт по одному HabitSchedule на каждое время.
        Иначе — один schedule с reminder_time.
        """
        name = validate_habit_name(name)
        if not name:
            return None
        times = reminder_times if reminder_times else [reminder_time]
        validated_times = [t for t in times if validate_time(t)]
        if not validated_times:
            validated_times = ["09:00"]
        habit = Habit(user_id=user_id, name=name, description=description, emoji=emoji)
        await self._repo.add(habit)
        days_str = days_of_week or ""
        for t in validated_times:
            sched = HabitSchedule(
                habit_id=habit.id,
                schedule_type=schedule_type,
                reminder_time=t,
                days_of_week=days_str or None,
            )
            self._session.add(sched)
        await self._session.flush()
        await self._session.refresh(habit)
        return habit

    async def log_complete(self, habit_id: int, user_id: int, log_date: date | None = None) -> HabitLog | None:
        """Log habit as completed."""
        habit = await self._repo.get_with_schedules(habit_id, user_id)
        if not habit:
            return None
        d = log_date or date.today()
        existing = await self._repo.get_habit_log(habit_id, d)
        if existing:
            existing.completed = True
            existing.decline_note_id = None
            await self._session.flush()
            await self._session.refresh(existing)
            return existing
        log = HabitLog(habit_id=habit_id, log_date=d, completed=True)
        await self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def log_decline(
        self, habit_id: int, user_id: int, note: str | None = None, preset: str | None = None
    ) -> HabitLog | None:
        """Log habit as declined (skipped)."""
        habit = await self._repo.get_with_schedules(habit_id, user_id)
        if not habit:
            return None
        d = date.today()
        existing = await self._repo.get_habit_log(habit_id, d)
        if existing:
            existing.completed = False
            if note or preset:
                dn = HabitDeclineNote(note=note or preset or "—", preset=preset)
                self._session.add(dn)
                await self._session.flush()
                existing.decline_note_id = dn.id
            await self._session.flush()
            await self._session.refresh(existing)
            return existing
        decline_note = None
        if note or preset:
            decline_note = HabitDeclineNote(note=note or preset or "—", preset=preset)
            self._session.add(decline_note)
            await self._session.flush()
        log = HabitLog(
            habit_id=habit_id,
            log_date=d,
            completed=False,
            decline_note_id=decline_note.id if decline_note else None,
        )
        await self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log
