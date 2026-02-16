"""Loyalty / referral program."""

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.services import user_service
from app.texts import t

router = Router(name="loyalty")


def _referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


@router.callback_query(lambda c: c.data == "loyalty")
async def cb_loyalty(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code

    bot_info = await cb.bot.get_me()
    username = bot_info.username or "YourBot"
    link = _referral_link(username, user.id)

    text = t(lang, "loyalty_title") + "\n\n" + t(lang, "loyalty_link") + "\n" + link
    await cb.message.edit_text(text, reply_markup=back_only(lang))
