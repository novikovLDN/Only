"""Main menu — show main greeting and buttons."""

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import main_menu
from app.services import user_service
from app.texts import t
from app.utils.safe_edit import safe_edit_or_send

router = Router(name="main_menu")


@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "en"
        is_premium = user_service.is_premium(user) if user else False

    await safe_edit_or_send(
        cb,
        t(lang, "main_greeting").format(name=fname or "there"),
        reply_markup=main_menu(lang, is_premium),
    )
