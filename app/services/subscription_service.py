"""Subscription service."""

from datetime import datetime, timedelta, timezone

from app.core.enums import Tariff, TARIFF_DAYS
from app.core.models import User
from app.repositories.user_repo import UserRepository


class SubscriptionService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def is_active(self, user: User) -> bool:
        if user.subscription_until is None:
            return False
        return user.subscription_until > datetime.now(timezone.utc)

    async def extend(self, user: User, tariff: Tariff) -> None:
        days = TARIFF_DAYS[tariff]
        await self.user_repo.extend_subscription(user, days)
