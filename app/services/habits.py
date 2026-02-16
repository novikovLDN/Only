"""Habit service."""

from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit


async def create(
    session: AsyncSession,
    user_id: int,
    title: str,
    remind_time: time,
) -> Habit:
    habit = Habit(user_id=user_id, title=title, remind_time=remind_time)
    session.add(habit)
    await session.flush()
    await session.refresh(habit)
    return habit


async def get_user_habits(session: AsyncSession, user_id: int) -> list[Habit]:
    result = await session.execute(select(Habit).where(Habit.user_id == user_id, Habit.is_active == True))
    return list(result.scalars().unique().all())


async def get_by_id(session: AsyncSession, habit_id: int) -> Habit | None:
    result = await session.execute(select(Habit).where(Habit.id == habit_id))
    return result.scalar_one_or_none()
