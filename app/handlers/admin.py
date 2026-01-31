"""
Admin panel handlers.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func

from app.config import settings
from app.models.user import User
from app.models.habit import Habit

router = Router(name="admin")


class AdminFilter:
    """Filter: only admin users."""

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return message.from_user.id in settings.admin_id_list


@router.message(Command("admin"), AdminFilter())
async def cmd_admin(message: Message, session) -> None:
    """Admin dashboard — system status."""
    users_result = await session.execute(select(func.count(User.id)))
    habits_result = await session.execute(select(func.count(Habit.id)))
    users_count = users_result.scalar() or 0
    habits_count = habits_result.scalar() or 0
    text = (
        "📊 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📋 Привычек: {habits_count}\n\n"
        "Команды:\n"
        "/admin_logs — последние ошибки\n"
        "/admin_broadcast — рассылка"
    )
    await message.answer(text)
