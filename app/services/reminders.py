"""Reminder service — motivation phrases, habit logs."""

import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit, HabitLog, MotivationUsage, User

MOTIVATION_RU = [
    "Молодец!", "Так держать!", "Ты справляешься!", "Отличный шаг!", "Прекрасная работа!",
] * 30

MOTIVATION_EN = [
    "Well done!", "Keep it up!", "You're doing it!", "Great step!", "Great job!",
] * 30


def get_phrase(lang: str, used_indices: set[int]) -> tuple[str, int]:
    phrases = MOTIVATION_RU if lang == "ru" else MOTIVATION_EN
    available = [i for i in range(len(phrases)) if i not in used_indices]
    if not available:
        idx = random.randint(0, len(phrases) - 1)
        return phrases[idx], idx
    idx = random.choice(available)
    return phrases[idx], idx


async def record_phrase_usage(session: AsyncSession, user_id: int, phrase_index: int) -> None:
    usage = MotivationUsage(user_id=user_id, phrase_index=phrase_index)
    session.add(usage)
    await session.flush()


async def get_used_indices(session: AsyncSession, user_id: int) -> set[int]:
    result = await session.execute(
        select(MotivationUsage.phrase_index).where(MotivationUsage.user_id == user_id)
    )
    return set(result.scalars().all())


async def reset_usage_if_needed(session: AsyncSession, user_id: int, lang: str) -> None:
    phrases = MOTIVATION_RU if lang == "ru" else MOTIVATION_EN
    used = await get_used_indices(session, user_id)
    if len(used) >= len(phrases):
        from sqlalchemy import delete
        await session.execute(delete(MotivationUsage).where(MotivationUsage.user_id == user_id))
        await session.flush()


async def log_done(session: AsyncSession, habit_id: int, user_id: int, d: date) -> HabitLog:
    log = HabitLog(habit_id=habit_id, user_id=user_id, date=d, status="done")
    session.add(log)
    await session.flush()
    return log


async def log_skipped(session: AsyncSession, habit_id: int, user_id: int, d: date, reason: str) -> HabitLog:
    log = HabitLog(habit_id=habit_id, user_id=user_id, date=d, status="skipped", skip_reason=reason)
    session.add(log)
    await session.flush()
    return log


async def has_log_today(session: AsyncSession, user_id: int, habit_id: int, d: date) -> bool:
    result = await session.execute(
        select(HabitLog).where(
            HabitLog.user_id == user_id,
            HabitLog.habit_id == habit_id,
            HabitLog.date == d,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_pending_log(session: AsyncSession, log_id: int) -> HabitLog | None:
    result = await session.execute(select(HabitLog).where(HabitLog.id == log_id))
    return result.scalar_one_or_none()
