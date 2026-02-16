"""Profile screen."""

from datetime import datetime

from aiogram import Router
from aiogram.types import CallbackQuery

from app.db import get_session_maker
from app.keyboards import back_only, main_menu
from app.keyboards.profile import profile_keyboard
from app.services import habit_log_service, referral_service, user_service
from app.services.user_service import is_premium
from app.texts import t

router = Router(name="profile")


@router.callback_query(lambda c: c.data == "profile")
async def cb_profile(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    fname = cb.from_user.first_name if cb.from_user else ""

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        ref_count = await referral_service.count_referrals(session, user.id)
        done = await habit_log_service.count_done(session, user.id)
        skipped = await habit_log_service.count_skipped(session, user.id)

    from datetime import timezone
    premium_str = t(lang, "profile_no_premium")
    if user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > datetime.now(timezone.utc):
            premium_str = t(lang, "profile_premium_until").format(
                date=user.premium_until.strftime("%Y-%m-%d")
            )

    premium = is_premium(user)
    text = (
        t(lang, "profile_title").format(name=fname or "there")
        + f"\n\n{premium_str}\n"
        + t(lang, "profile_referrals").format(count=ref_count)
        + "\n\n"
        + t(lang, "profile_done").format(count=done)
        + "\n"
        + t(lang, "profile_skipped").format(count=skipped)
    )

    await cb.message.edit_text(text, reply_markup=profile_keyboard(lang, premium))


@router.callback_query(lambda c: c.data == "profile_missed")
async def cb_profile_missed(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code

    await cb.message.edit_text(t(lang, "profile_skipped"), reply_markup=back_only(lang, "profile"))
