"""Loyalty / referral program — Reply keyboard only."""

from aiogram import Router
from aiogram.types import Message

from app.keyboards.reply import loyalty_menu, main_menu

router = Router(name="loyalty")

BTN_BACK = ("🔙 Back", "🔙 Назад")
LOYALTY_SHARE = ("🔗 Поделиться ссылкой", "🔗 Share link")
LOYALTY_DETAILS = ("ℹ️ Подробнее", "ℹ️ Details")


async def build_loyalty_content(user, t, session, bot) -> tuple[str, type]:
    from app.repositories.referral_repo import ReferralRepository

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
    text = f"{t('loyalty.referral_link')}\n{link}\n\n{t('loyalty.invited_count', count=count)}\n\n{t('loyalty.info')}"
    return text, loyalty_menu(t)


async def send_loyalty_screen(message: Message, user, t, session) -> None:
    text, kb = await build_loyalty_content(user, t, session, message.bot)
    await message.answer(text, reply_markup=kb)


@router.message(F.text.in_(LOYALTY_SHARE))
async def share_link_btn(message: Message, user, t, session) -> None:
    username = "your_bot"
    if message.bot:
        try:
            me = await message.bot.get_me()
            username = me.username or "your_bot"
        except Exception:
            pass
    link = f"https://t.me/{username}?start=ref_{user.telegram_id}"
    await message.answer(link, reply_markup=main_menu(t))


@router.message(F.text.in_(LOYALTY_DETAILS))
async def loyalty_details_btn(message: Message, t) -> None:
    await message.answer(t("loyalty.info"), reply_markup=main_menu(t))
