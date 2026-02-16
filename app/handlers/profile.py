"""Profile screen — single message with photo."""

from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import CallbackQuery

from app.core.levels import get_required_xp
from app.db import get_session_maker
from app.keyboards import back_only
from app.keyboards.profile import profile_keyboard
from app.utils.progress import build_progress_bar
from app.utils.safe_edit import safe_edit_or_send
from app.services import habit_log_service, referral_service, user_service
from app.texts import t

router = Router(name="profile")


def _build_profile_caption(user, lang: str, ref_count: int, done: int, skipped: int, fname: str = "") -> str:
    premium_str = t(lang, "profile_no_premium")
    if user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > datetime.now(timezone.utc):
            premium_str = t(lang, "profile_premium_until").format(
                date=user.premium_until.strftime("%Y-%m-%d")
            )
    xp = getattr(user, "xp", 0) or 0
    level = getattr(user, "level", 1) or 1
    required = get_required_xp(level)
    progress = build_progress_bar(xp, required)
    name = fname or getattr(user, "first_name", None) or "there"
    return (
        t(lang, "profile_title").format(name=name)
        + f"\n\n{premium_str}\n"
        + t(lang, "profile_referrals").format(count=ref_count)
        + "\n\n"
        + t(lang, "your_level") + f": {level}\n{progress}\n\n"
        + t(lang, "profile_done").format(count=done)
        + "\n"
        + t(lang, "profile_skipped").format(count=skipped)
    )


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

    is_premium = user_service.is_premium(user)
    caption = _build_profile_caption(user, lang, ref_count, done, skipped, fname or "")
    kb = profile_keyboard(lang, is_premium)

    # Edit in place (from main menu or Back from statistics/achievements)
    await safe_edit_or_send(cb, caption, reply_markup=kb)


@router.callback_query(lambda c: c.data == "profile_statistics")
async def cb_profile_statistics(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        done = await habit_log_service.count_done(session, user.id)
        skipped = await habit_log_service.count_skipped(session, user.id)

    text = (
        f"📊 {t(lang, 'statistics')}\n\n"
        f"✅ {t(lang, 'done_habits')}: {done}\n"
        f"⏭ {t(lang, 'skipped_habits')}: {skipped}"
    )
    await safe_edit_or_send(cb, text, reply_markup=back_only(lang, "profile"))


@router.callback_query(lambda c: c.data == "profile_achievements")
async def cb_profile_achievements(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        done = await habit_log_service.count_done(session, user.id)
        streak = await habit_log_service.get_max_streak(session, user.id)

    a10 = "✅" if done >= 10 else "🔒"
    a50 = "✅" if done >= 50 else "🔒"
    a100 = "✅" if done >= 100 else "🔒"
    a_streak = "✅" if streak >= 10 else "🔒"

    text = (
        f"{t(lang, 'achievements_title')}\n\n"
        f"{a10} {t(lang, 'ach_10_habits')}\n"
        f"{a50} {t(lang, 'ach_50_habits')}\n"
        f"{a100} {t(lang, 'ach_100_habits')}\n"
        f"{a_streak} {t(lang, 'ach_10_streak')}"
    )
    await safe_edit_or_send(cb, text, reply_markup=back_only(lang, "profile"))


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

    await safe_edit_or_send(cb, t(lang, "profile_skipped"), reply_markup=back_only(lang, "profile"))
