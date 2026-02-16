"""Habit log service."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HabitLog


async def has_log_today(
    session: AsyncSession,
    user_id: int,
    habit_id: int,
    today: date,
) -> bool:
    result = await session.execute(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id,
            HabitLog.user_id == user_id,
            HabitLog.log_date == today,
        )
    )
    return result.scalar_one_or_none() is not None


async def log_done(
    session: AsyncSession,
    habit_id: int,
    user_id: int,
    today: date,
) -> HabitLog:
    log = HabitLog(habit_id=habit_id, user_id=user_id, log_date=today, status="done")
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


async def log_skipped(
    session: AsyncSession,
    habit_id: int,
    user_id: int,
    today: date,
) -> HabitLog:
    log = HabitLog(habit_id=habit_id, user_id=user_id, log_date=today, status="skipped")
    session.add(log)
    await session.flush()
    await session.refresh(log)
    return log


async def count_done(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func
    result = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.status == "done",
        )
    )
    return result.scalar() or 0


async def count_skipped(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func
    result = await session.execute(
        select(func.count()).select_from(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.status == "skipped",
        )
    )
    return result.scalar() or 0
