"""Profile handler — inline only."""

from aiogram import Router
from aiogram.types import Message

from app.keyboards.inline import back_inline

router = Router(name="profile")


async def show_profile(message: Message, user, t, session=None) -> None:
    from app.core.database import get_session_maker
    from app.repositories.referral_repo import ReferralRepository

    lang = user.language or "en"
    if session:
        ref_repo = ReferralRepository(session)
        count = await ref_repo.count_by_inviter(user.id)
    else:
        sm = get_session_maker()
        async with sm() as s:
            ref_repo = ReferralRepository(s)
            count = await ref_repo.count_by_inviter(user.id)

    reg_date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    sub_until = (
        user.subscription_until.strftime("%d.%m.%Y")
        if user.subscription_until
        else t("no_subscription")
    )
    text = (
        f"{t('profile')}\n"
        f"{t('registration_date', date=reg_date)}\n"
        f"{t('invited_count', count=count)}\n"
        f"{t('subscription_until', date=sub_until)}"
    )
    await message.answer(text, reply_markup=back_inline(lang))
