"""Motivation phrase repository."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import MotivationPhrase


class MotivationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_unused(self, language: str) -> MotivationPhrase | None:
        result = await self.session.execute(
            select(MotivationPhrase)
            .where(MotivationPhrase.language == language, MotivationPhrase.is_used == False)
            .order_by(func.random())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def reset_all_for_language(self, language: str) -> None:
        await self.session.execute(
            update(MotivationPhrase).where(MotivationPhrase.language == language).values(is_used=False)
        )
        await self.session.flush()

    async def mark_used(self, phrase: MotivationPhrase) -> None:
        phrase.is_used = True
        await self.session.flush()
