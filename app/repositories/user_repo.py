"""
User repository.
"""

import secrets
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import UserTier
from app.config.settings import settings
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID."""
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> User | None:
        """Get user by referral code."""
        result = await self._session.execute(select(User).where(User.referral_code == code))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str = "",
        last_name: str | None = None,
        language_code: str = "en",
        referral_code: str | None = None,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        Returns (user, created).
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Update fields
            user.username = username
            user.first_name = first_name or user.first_name
            user.last_name = last_name
            user.language_code = language_code or user.language_code
            await self._session.flush()
            await self._session.refresh(user)
            return user, False

        from datetime import timedelta, timezone

        ref_code = self._generate_referral_code()
        trial_ends = datetime.now(timezone.utc) + timedelta(days=settings.trial_days)

        user = User(
            id=telegram_id,  # Use telegram_id as id for simplicity
            telegram_id=telegram_id,
            username=username,
            first_name=first_name or "User",
            last_name=last_name,
            language_code=language_code or "en",
            tier=UserTier.TRIAL,
            trial_ends_at=trial_ends,
            referral_code=ref_code,
        )
        await self.add(user)
        return user, True

    async def count_all(self) -> int:
        """Total users count."""
        result = await self._session.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def count_by_tier(self, tier: str) -> int:
        """Count users by tier."""
        result = await self._session.execute(
            select(func.count(User.id)).where(User.tier == tier)
        )
        return result.scalar() or 0

    async def count_created_since_days(self, days: int) -> int:
        """Count users registered in last N days."""
        from datetime import timedelta, timezone

        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._session.execute(
            select(func.count(User.id)).where(User.created_at >= since)
        )
        return result.scalar() or 0

    def _generate_referral_code(self) -> str:
        """Generate unique referral code."""
        return secrets.token_urlsafe(16)[:16]
