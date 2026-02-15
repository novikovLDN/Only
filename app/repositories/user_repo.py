"""User repository."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Referral, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        language: str | None = None,
        invited_by_id: int | None = None,
    ) -> User:
        lang = language if language in ("ru", "en") else "ru"
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=lang,
            invited_by_id=invited_by_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language: str | None = None,
        invited_by_id: int | None = None,
    ) -> tuple[User, bool]:
        user = await self.session.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        if user:
            return user, False

        lang = language if language in ("ru", "en") else "ru"
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name or "",
            language=lang,
            invited_by_id=invited_by_id,
            timezone="UTC",
            is_active=True,
        )
        self.session.add(user)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return user, True

    async def update_language(self, user: User, language: str) -> None:
        user.language = language if language in ("ru", "en") else "ru"
        await self.session.flush()

    async def extend_subscription(self, user: User, days: int) -> None:
        now = datetime.now(timezone.utc)
        base = (max(user.subscription_until, now) if user.subscription_until and user.subscription_until > now else now)
        user.subscription_until = base + timedelta(days=days)
        await self.session.flush()

    async def get_by_id_for_update(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id).with_for_update())
        return result.scalar_one_or_none()

    async def count_referrals(self, user_id: int) -> int:
        result = await self.session.execute(
            select(Referral).where(Referral.inviter_id == user_id)
        )
        return len(result.scalars().all())
