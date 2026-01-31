"""
Achievement repository.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement


class AchievementRepository:
    """Achievement data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Achievement]:
        """All achievements ordered by id."""
        result = await self._session.execute(
            select(Achievement).order_by(Achievement.id)
        )
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Achievement | None:
        """Achievement by code."""
        result = await self._session.execute(
            select(Achievement).where(Achievement.code == code)
        )
        return result.scalar_one_or_none()

    async def get_unlocked_ids(self, user_id: int) -> set[int]:
        """Set of achievement IDs user has unlocked."""
        result = await self._session.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        )
        return {r[0] for r in result.all()}

    async def unlock(self, user_id: int, achievement_id: int) -> UserAchievement | None:
        """Unlock achievement for user. Returns UserAchievement or None if already unlocked."""
        existing = await self._session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        if existing.scalar_one_or_none():
            return None
        ua = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            unlocked_at=datetime.now(timezone.utc),
        )
        self._session.add(ua)
        await self._session.flush()
        await self._session.refresh(ua)
        return ua
