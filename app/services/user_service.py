"""
User service — tier, trial, limits.
"""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import UserTier
from app.config.settings import settings
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.habit_repo import HabitRepository
from app.repositories.subscription_repo import SubscriptionRepository


class UserService:
    """User business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._habit_repo = HabitRepository(session)
        self._sub_repo = SubscriptionRepository(session)

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str = "",
        last_name: str | None = None,
        language_code: str = "en",
        referral_code: str | None = None,
    ) -> tuple[User, bool]:
        """Get or create user. Returns (user, created)."""
        return await self._user_repo.get_or_create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            referral_code=referral_code,
        )

    async def get_user(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID."""
        return await self._user_repo.get_by_telegram_id(telegram_id)

    def get_habits_limit(self, user: User) -> int:
        """Get max habits allowed for user tier."""
        if user.tier == UserTier.PREMIUM:
            return settings.premium_habits_limit
        if user.tier == UserTier.TRIAL:
            return 3
        return settings.free_habits_limit

    async def can_add_habit(self, user: User) -> tuple[bool, str]:
        """
        Check if user can add another habit.
        Returns (allowed, reason_if_not).
        """
        limit = self.get_habits_limit(user)
        count = await self._habit_repo.count_user_habits(user.id)
        if count >= limit:
            from app.texts import LIMIT_HABITS
            return False, LIMIT_HABITS.format(limit=limit)
        return True, ""

    async def refresh_tier(self, user: User) -> User:
        """Refresh user tier from trial/subscription state."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if user.tier == UserTier.TRIAL and user.trial_ends_at and user.trial_ends_at <= now:
            user.tier = UserTier.FREE
            user.trial_ends_at = None
            await self._session.flush()
        sub = await self._sub_repo.get_active_subscription(user.id)
        if sub:
            user.tier = UserTier.PREMIUM
            await self._session.flush()
        await self._session.refresh(user)
        return user
