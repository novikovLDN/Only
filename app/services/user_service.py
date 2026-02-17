"""User service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_maker
from app.models import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_premium(user: User) -> bool:
    if not user.premium_until:
        return False
    pu = user.premium_until
    if pu.tzinfo is None:
        pu = pu.replace(tzinfo=timezone.utc)
    return pu > _now()


async def get_or_create(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    telegram_language_code: str | None = None,
) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        return user, False

    lang = (telegram_language_code or "ru")[:2].lower() if telegram_language_code else "ru"
    if lang not in ("ru", "en", "ar"):
        lang = "ru"

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        language_code=lang,
        timezone="Europe/Moscow",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_language(session: AsyncSession, user: User, language_code: str) -> None:
    user.language_code = language_code if language_code in ("ru", "en", "ar") else "ru"
    await session.flush()


ALLOWED_TIMEZONES = {"Europe/Moscow", "Europe/London", "America/New_York", "Asia/Dubai"}


def _validate_iana_timezone(tz: str) -> str:
    """Only 4 TZ allowed. Returns Europe/Moscow if invalid."""
    tz = (tz or "Europe/Moscow").strip()
    return tz if tz in ALLOWED_TIMEZONES else "Europe/Moscow"


async def update_timezone(session: AsyncSession, user: User, timezone: str) -> None:
    """Update user timezone. IANA only. Falls back to UTC if invalid."""
    tz = _validate_iana_timezone(timezone)
    user.timezone = tz
    await session.flush()


async def update_user_timezone(user_id: int, new_tz: str) -> bool:
    """
    Standalone update by user.id. Validates IANA, commits immediately.
    Single source of truth for TZ changes.
    """
    tz = _validate_iana_timezone(new_tz)
    sm = get_session_maker()
    async with sm() as session:
        result = await session.execute(update(User).where(User.id == user_id).values(timezone=tz))
        await session.commit()
        return result.rowcount > 0


async def extend_premium(session: AsyncSession, user: User, months: int) -> None:
    now = _now()
    if user.premium_until and user.premium_until > now:
        user.premium_until = user.premium_until + timedelta(days=months * 30)
    else:
        user.premium_until = now + timedelta(days=months * 30)
    await session.flush()


async def add_reward_days(session: AsyncSession, user: User, days: int) -> None:
    user.premium_reward_days = (user.premium_reward_days or 0) + days
    if user.premium_until and (user.premium_until.replace(tzinfo=timezone.utc) if user.premium_until.tzinfo is None else user.premium_until) > _now():
        user.premium_until = user.premium_until + timedelta(days=days)
    else:
        user.premium_until = _now() + timedelta(days=days)
    await session.flush()
