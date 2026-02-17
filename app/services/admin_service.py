"""Admin service — full user delete with cascade."""

from sqlalchemy import select

from app.db import get_session_maker
from app.models import User


async def delete_user_full_by_tg_id(tg_id: int) -> bool:
    """
    Delete user and all related data by Telegram ID.
    Relies on ON DELETE CASCADE for habits, logs, payments, referrals, etc.
    Transactional and atomic.
    """
    sm = get_session_maker()
    async with sm() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        await session.delete(user)
        await session.commit()

    return True
