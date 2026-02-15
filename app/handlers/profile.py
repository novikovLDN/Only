"""Profile."""

from aiogram import Router
from aiogram.types import Message

from app.keyboards.inline import profile_menu

router = Router(name="profile")


async def build_profile_content(user, t, session) -> tuple[str, "InlineKeyboardMarkup"]:
    from app.repositories.referral_repo import ReferralRepository
    from datetime import datetime, timezone

    ref_repo = ReferralRepository(session)
    count = await ref_repo.count_by_inviter(user.id)
    reg_date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    sub_until = (
        user.subscription_until.strftime("%d.%m.%Y")
        if user.subscription_until
        else t("profile.no_subscription")
    )
    has_sub = user.subscription_until and user.subscription_until > datetime.now(timezone.utc)
    text = (
        f"{t('profile.title')}\n"
        f"{t('profile.registration', date=reg_date)}\n"
        f"{t('profile.invited', count=count)}\n"
        f"{t('profile.subscription_until', date=sub_until)}"
    )
    return text, profile_menu(t, has_sub)


async def show_profile(message: Message, user, t, session=None) -> None:
    text, kb = await build_profile_content(user, t, session)
    await message.answer(text, reply_markup=kb)
