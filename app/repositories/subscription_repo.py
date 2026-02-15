"""Subscription-related queries (users table)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscription_until(self, user_id: int) -> datetime | None:
        result = await self.session.execute(
            select(User.subscription_until).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
