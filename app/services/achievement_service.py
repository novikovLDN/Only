"""
Achievement service — проверка и разблокировка достижений.
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import AchievementConditionType, UserTier
from app.models.achievement import Achievement
from app.models.user import User
from app.repositories.achievement_repo import AchievementRepository
from app.repositories.habit_repo import HabitRepository


class AchievementService:
    """Achievement business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._achievement_repo = AchievementRepository(session)
        self._habit_repo = HabitRepository(session)

    async def check_and_unlock(self, user: User) -> Achievement | None:
        """
        Check all achievements, unlock any newly earned.
        Returns newly unlocked achievement or None.
        """
        unlocked_ids = await self._achievement_repo.get_unlocked_ids(user.id)
        achievements = await self._achievement_repo.get_all()

        created = await self._habit_repo.count_user_habits(user.id)
        completed = await self._habit_repo.count_user_completed_logs(user.id)
        streak = await self._habit_repo.get_current_streak(user.id)
        no_skips_7 = await self._habit_repo.has_no_skips_last_7_days(user.id)

        is_premium = user.tier == UserTier.PREMIUM

        for ach in achievements:
            if ach.id in unlocked_ids:
                continue
            if ach.is_premium and not is_premium:
                continue
            if not self._check_condition(ach, created, completed, streak, no_skips_7):
                continue
            ua = await self._achievement_repo.unlock(user.id, ach.id)
            if ua:
                return ach
        return None

    def _check_condition(
        self,
        ach: Achievement,
        created: int,
        completed: int,
        streak: int,
        no_skips_7: bool,
    ) -> bool:
        if ach.condition_type == AchievementConditionType.CREATED_HABITS:
            return created >= ach.condition_value
        if ach.condition_type == AchievementConditionType.STREAK:
            return streak >= ach.condition_value
        if ach.condition_type == AchievementConditionType.COMPLETED_HABITS:
            return completed >= ach.condition_value
        if ach.condition_type == AchievementConditionType.NO_SKIPS_7_DAYS:
            return no_skips_7
        return False
