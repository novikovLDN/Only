"""Data export handler — GDPR data portability."""

import io
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.db import get_session_maker
from app.services import user_service
from app.services.export_service import export_user_data
from app.texts import t

logger = logging.getLogger(__name__)

router = Router(name="export")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """Export all user data as a JSON file."""
    tid = message.from_user.id if message.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"

        await message.answer(t(lang, "export_preparing"))
        json_data = await export_user_data(session, user)

    file = BufferedInputFile(
        json_data.encode("utf-8"),
        filename=f"habit_data_{tid}.json",
    )
    await message.answer_document(file, caption=t(lang, "export_ready"))


@router.callback_query(F.data == "export_data")
async def cb_export(cb: CallbackQuery) -> None:
    """Export via settings menu button."""
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"

        json_data = await export_user_data(session, user)

    file = BufferedInputFile(
        json_data.encode("utf-8"),
        filename=f"habit_data_{tid}.json",
    )
    await cb.message.answer_document(file, caption=t(lang, "export_ready"))
