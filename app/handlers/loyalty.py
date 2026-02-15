"""Loyalty / referral program."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.inline import loyalty_menu, back_only

router = Router(name="loyalty")


async def build_loyalty_content(user, t, session, bot) -> tuple[str, "InlineKeyboardMarkup"]:
    from app.repositories.referral_repo import ReferralRepository
    from aiogram.types import InlineKeyboardMarkup

    ref_repo = ReferralRepository(session)
    count = await ref_repo.count_by_inviter(user.id)
    username = "your_bot"
    if bot:
        try:
            me = await bot.get_me()
            username = me.username or "your_bot"
        except Exception:
            pass
    link = f"https://t.me/{username}?start=ref_{user.telegram_id}"
    text = f"{t('referral_link')}\n{link}\n\n{t('invited_count', count=count)}\n\n{t('referral_info')}"
    return text, loyalty_menu(t)


@router.callback_query(F.data == "share_link")
async def share_link_cb(callback: CallbackQuery, user, t, session) -> None:
    bot = callback.message.bot
    username = "your_bot"
    if bot:
        try:
            me = await bot.get_me()
            username = me.username or "your_bot"
        except Exception:
            pass
    link = f"https://t.me/{username}?start=ref_{user.telegram_id}"
    await callback.answer()
    await callback.message.answer(link)


@router.callback_query(F.data == "loyalty_details")
async def loyalty_details_cb(callback: CallbackQuery, user, t) -> None:
    await callback.message.edit_text(t("referral_info"), reply_markup=back_only(t, "loyalty"))
    await callback.answer()
