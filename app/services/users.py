"""User service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


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
    if lang not in ("ru", "en"):
        lang = "ru"

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        language_code=lang,
        timezone="UTC",
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user, True


async def update_language(session: AsyncSession, user: User, language_code: str) -> None:
    user.language_code = "ru" if language_code not in ("ru", "en") else language_code
    await session.flush()


async def update_timezone(session: AsyncSession, user: User, timezone: str) -> None:
    user.timezone = timezone or "UTC"
    await session.flush()
