"""Habit repository."""

from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Habit, HabitDay, HabitTime


class HabitRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_habits(self, user_id: int) -> list[Habit]:
        result = await self.session.execute(
            select(Habit)
            .where(Habit.user_id == user_id)
            .options(selectinload(Habit.days), selectinload(Habit.times))
        )
        return list(result.scalars().unique().all())

    async def get_by_id(self, habit_id: int) -> Habit | None:
        result = await self.session.execute(
            select(Habit)
            .where(Habit.id == habit_id)
            .options(selectinload(Habit.days), selectinload(Habit.times))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        title: str,
        is_custom: bool,
        weekdays: list[int],
        times: list[time],
    ) -> Habit:
        habit = Habit(user_id=user_id, title=title, is_custom=is_custom)
        self.session.add(habit)
        await self.session.flush()
        for wd in weekdays:
            self.session.add(HabitDay(habit_id=habit.id, weekday=wd))
        for t in times:
            self.session.add(HabitTime(habit_id=habit.id, time=t))
        await self.session.flush()
        return habit

    async def update_days(self, habit: Habit, weekdays: list[int]) -> None:
        for d in habit.days:
            await self.session.delete(d)
        for wd in weekdays:
            self.session.add(HabitDay(habit_id=habit.id, weekday=wd))
        await self.session.flush()

    async def update_times(self, habit: Habit, times: list[time]) -> None:
        for t in habit.times:
            await self.session.delete(t)
        for t in times:
            self.session.add(HabitTime(habit_id=habit.id, time=t))
        await self.session.flush()

    async def delete(self, habit: Habit) -> None:
        await self.session.delete(habit)
        await self.session.flush()

    async def count_user_habits(self, user_id: int) -> int:
        result = await self.session.execute(select(Habit).where(Habit.user_id == user_id))
        return len(result.scalars().all())

    async def get_all_for_reminders(self) -> list[tuple[Habit, "User", list[int], list[time]]]:
        from app.core.models import User
        result = await self.session.execute(
            select(Habit, User)
            .join(User, User.id == Habit.user_id)
            .options(selectinload(Habit.days), selectinload(Habit.times))
        )
        out = []
        for h, u in result.all():
            days = [d.weekday for d in h.days]
            times = [t.time for t in h.times]
            out.append((h, u, days, times))
        return out
