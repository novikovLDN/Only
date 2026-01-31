"""
Admin dashboard handlers — /admin, inline navigation.
"""

import logging
from collections import defaultdict
from time import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.texts import ERROR_RATE_LIMIT
from app.keyboards.admin import (
    CALLBACK_PREFIX,
    admin_back_keyboard,
    admin_main_keyboard,
)
from app.services.admin_dashboard_service import AdminDashboardService

logger = logging.getLogger(__name__)

router = Router(name="admin")

# Admin rate limit: max 20 requests per minute (dashboard clicks)
ADMIN_RATE_LIMIT = 20


class AdminFilter:
    """Filter: only admin users."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return False
        return user_id in settings.admin_id_list


def _check_admin_rate_limit(user_id: int) -> bool:
    """Return True if within limit."""
    now = time()
    timestamps = _admin_timestamps[user_id]
    timestamps[:] = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= ADMIN_RATE_LIMIT:
        return False
    timestamps.append(now)
    return True


_admin_timestamps: dict[int, list[float]] = defaultdict(list)


async def _edit_or_send(event: Message | CallbackQuery, text: str, keyboard=None) -> None:
    """Edit message for callback, answer for message."""
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await event.message.answer(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)


@router.message(Command("admin"), AdminFilter())
async def cmd_admin(message: Message, session) -> None:
    """Admin dashboard — main menu."""
    if not _check_admin_rate_limit(message.from_user.id):
        await message.answer(ERROR_RATE_LIMIT)
        return
    text = "📊 <b>Admin Dashboard</b>\n\nВыбери раздел:"
    await message.answer(text, reply_markup=admin_main_keyboard())


@router.callback_query(F.data.startswith(CALLBACK_PREFIX), AdminFilter())
async def admin_callback(callback: CallbackQuery, session) -> None:
    """Handle admin section callbacks."""
    if not _check_admin_rate_limit(callback.from_user.id):
        await callback.answer(ERROR_RATE_LIMIT, show_alert=True)
        return
    data = callback.data[len(CALLBACK_PREFIX) :]
    svc = AdminDashboardService(session)
    back_kb = admin_back_keyboard()
    bot_alive = True
    try:
        await callback.bot.get_me()
    except Exception:
        bot_alive = False
    try:
        if data == "back":
            text = "📊 <b>Admin Dashboard</b>\n\nВыбери раздел:"
            await _edit_or_send(callback, text, admin_main_keyboard())
            return
        if data == "system":
            text = await svc.get_system_status(bot_alive=bot_alive)
        elif data == "users":
            text = await svc.get_users_stats()
        elif data == "subs":
            text = await svc.get_subscriptions_stats()
        elif data == "finance":
            text = await svc.get_finance_stats()
        elif data == "analytics":
            text = await svc.get_analytics()
        elif data == "errors":
            text = await svc.get_errors_alerts(limit=5)
        else:
            text = "Неизвестный раздел"
        await _edit_or_send(callback, text, back_kb)
    except Exception as e:
        logger.exception("Admin dashboard error: %s", e)
        await _edit_or_send(
            callback,
            f"❌ Ошибка: {str(e)[:100]}",
            back_kb,
        )
