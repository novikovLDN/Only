"""Habit log repository — completion, decline, missed."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import HabitLog


class HabitLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_habit_date(self, user_id: int, habit_id: int, d: date) -> HabitLog | None:
        result = await self.session.execute(
            select(HabitLog).where(
                HabitLog.user_id == user_id,
                HabitLog.habit_id == habit_id,
                HabitLog.date == d,
            )
        )
        return result.scalar_one_or_none()

    async def exists_for_user_habit_date(self, user_id: int, habit_id: int, d: date) -> bool:
        log = await self.get_by_user_habit_date(user_id, habit_id, d)
        return log is not None

    async def create_pending(self, user_id: int, habit_id: int, d: date) -> HabitLog:
        log = HabitLog(user_id=user_id, habit_id=habit_id, date=d, status="pending")
        self.session.add(log)
        await self.session.flush()
        return log

    async def mark_completed(self, log: HabitLog) -> None:
        log.status = "completed"
        await self.session.flush()

    async def mark_declined(self, log: HabitLog, reason: str) -> None:
        log.status = "declined"
        log.reason = reason
        await self.session.flush()

    async def mark_missed(self, log: HabitLog) -> None:
        log.status = "missed"
        await self.session.flush()

    async def get_by_id(self, log_id: int) -> HabitLog | None:
        result = await self.session.execute(select(HabitLog).where(HabitLog.id == log_id))
        return result.scalar_one_or_none()

    async def get_pending_for_user(self, user_id: int) -> HabitLog | None:
        result = await self.session.execute(
            select(HabitLog)
            .where(HabitLog.user_id == user_id, HabitLog.status == "pending")
            .order_by(HabitLog.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
