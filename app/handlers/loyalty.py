"""Loyalty / referral program — inline only."""

from aiogram import Router
from aiogram.types import Message

from app.keyboards.inline import back_inline

router = Router(name="loyalty")


async def _get_loyalty_content(user, t, session=None, bot=None) -> tuple[str, "InlineKeyboardMarkup"]:
    from app.repositories.referral_repo import ReferralRepository
    from aiogram.types import InlineKeyboardMarkup

    lang = user.language or "en"
    if session is None:
        from app.core.database import get_session_maker
        sm = get_session_maker()
        async with sm() as s:
            ref_repo = ReferralRepository(s)
            count = await ref_repo.count_by_inviter(user.id)
    else:
        ref_repo = ReferralRepository(session)
        count = await ref_repo.count_by_inviter(user.id)

    username = "your_bot"
    if bot:
        try:
            me = await bot.get_me()
            username = me.username if me else "your_bot"
        except Exception:
            pass

    link = f"https://t.me/{username}?start=ref_{user.telegram_id}"
    text = f"{t('referral_link')}\n{link}\n\n{t('invited_count', count=count)}"
    return text, back_inline(lang)


async def show_loyalty(message: Message, user, t, session=None) -> None:
    bot = getattr(message, "bot", None)
    text, kb = await _get_loyalty_content(user, t, session, bot)
    await message.answer(text, reply_markup=kb)
