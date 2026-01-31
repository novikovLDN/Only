"""
Retention paywall — умные триггеры под подписку.
Не чаще 1 сообщения в 24ч.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import UserTier
from app.models.user import User
from app.repositories.achievement_repo import AchievementRepository


PAYWALL_COOLDOWN_HOURS = 24


class RetentionPaywallService:
    """Smart paywall triggers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._achievement_repo = AchievementRepository(session)

    async def should_show_paywall(self, user: User) -> tuple[bool, str | None]:
        """
        Check if we should show paywall.
        Returns (should_show, message_key).
        """
        if user.tier == UserTier.PREMIUM:
            return False, None
        if not self._can_show_now(user):
            return False, None
        if await self._trigger_profile_5(user):
            return True, "profile_5"
        if await self._trigger_achievements_2(user):
            return True, "achievements_2"
        if await self._trigger_streak_5(user):
            return True, "streak_5"
        if await self._trigger_trial_ending(user):
            return True, "trial_ending"
        return False, None

    def _can_show_now(self, user: User) -> bool:
        last = getattr(user, "last_paywall_shown_at", None)
        if not last:
            return True
        if last.tzinfo is None:
            from datetime import timezone as tz
            last = last.replace(tzinfo=tz.utc)
        return (datetime.now(timezone.utc) - last) > timedelta(hours=PAYWALL_COOLDOWN_HOURS)

    async def _trigger_profile_5(self, user: User) -> bool:
        count = getattr(user, "profile_views_count", 0)
        return count >= 5

    async def _trigger_achievements_2(self, user: User) -> bool:
        unlocked = await self._achievement_repo.get_unlocked_ids(user.id)
        return len(unlocked) >= 2

    async def _trigger_streak_5(self, user: User) -> bool:
        from app.repositories.habit_repo import HabitRepository
        repo = HabitRepository(self._session)
        streak = await repo.get_current_streak(user.id)
        return streak >= 5

    async def _trigger_trial_ending(self, user: User) -> bool:
        if user.tier != UserTier.TRIAL or not user.trial_ends_at:
            return False
        ends = user.trial_ends_at
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        delta = (ends - datetime.now(timezone.utc)).total_seconds() / 3600
        return 0 < delta <= 24
