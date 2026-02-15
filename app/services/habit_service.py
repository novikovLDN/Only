"""Habit service."""

from datetime import time

from app.core.constants import FREE_HABITS_LIMIT
from app.core.models import Habit, User
from app.repositories.habit_repo import HabitRepository


class HabitService:
    def __init__(self, repo: HabitRepository, user_repo):
        self.repo = repo
        self.user_repo = user_repo

    def _is_premium(self, user: User) -> bool:
        if user.subscription_until is None:
            return False
        from datetime import datetime, timezone
        return user.subscription_until > datetime.now(timezone.utc)

    async def can_add_habit(self, user: User) -> bool:
        count = await self.repo.count_user_habits(user.id)
        return count < FREE_HABITS_LIMIT or self._is_premium(user)

    async def can_add_custom(self, user: User) -> bool:
        return self._is_premium(user)

    async def create_habit(
        self,
        user: User,
        title: str,
        is_custom: bool,
        weekdays: list[int],
        times: list[time],
    ) -> Habit:
        return await self.repo.create(
            user.id, title, is_custom, weekdays, times
        )

    async def get_user_habits(self, user_id: int) -> list[Habit]:
        return await self.repo.get_user_habits(user_id)

    async def get_habit(self, habit_id: int) -> Habit | None:
        return await self.repo.get_by_id(habit_id)

    async def update_days(self, habit: Habit, weekdays: list[int]) -> None:
        await self.repo.update_days(habit, weekdays)

    async def update_times(self, habit: Habit, times: list[time]) -> None:
        await self.repo.update_times(habit, times)

    async def delete_habit(self, habit: Habit) -> None:
        await self.repo.delete(habit)
