"""Profile screen — single message with photo + caption."""

from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.core.levels import get_required_xp
from app.db import get_session_maker
from app.keyboards import back_only
from app.keyboards.profile import profile_keyboard
from app.utils.progress import build_progress_bar
from app.utils.safe_edit import safe_edit_or_send
from app.services import habit_log_service, referral_service, user_service
from app.texts import t

router = Router(name="profile")


def _format_date_ru(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y")


def _format_date_en(dt: datetime) -> str:
    return dt.strftime("%d %B %Y")


def _build_profile_caption(user, lang: str, ref_count: int, fname: str = "") -> str:
    """Build profile caption with emojis. One message: photo + caption."""
    lang = "en" if (lang or "").lower() == "en" else "ru"
    name = fname or getattr(user, "first_name", None) or "there"

    if user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > datetime.now(timezone.utc):
            premium_date = _format_date_ru(pu) if lang == "ru" else _format_date_en(pu)
        else:
            premium_date = "—"
    else:
        premium_date = "—"

    xp = getattr(user, "xp", 0) or 0
    level = getattr(user, "level", 1) or 1
    required = get_required_xp(level)
    progress = build_progress_bar(xp, required)

    if lang == "ru":
        return (
            f"👋 Рады тебя видеть, {name}!\n\n"
            f"💎 Подписка активна до: {premium_date}\n"
            f"🤝 Приглашено друзей: {ref_count}\n\n"
            f"⭐ Ваш уровень: {level}\n{progress}"
        )
    return (
        f"👋 Glad to see you, {name}!\n\n"
        f"💎 Premium active until: {premium_date}\n"
        f"🤝 Friends invited: {ref_count}\n\n"
        f"⭐ Your level: {level}\n{progress}"
    )


async def _send_profile(target, user, ref_count: int, fname: str, lang: str, is_premium: bool) -> None:
    """Send profile as ONE message: photo + caption, or text only. No edit_text."""
    caption = _build_profile_caption(user, lang, ref_count, fname)
    kb = profile_keyboard(lang, is_premium)
    tid = user.telegram_id
    try:
        photos = await target.bot.get_user_profile_photos(tid, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            await target.answer_photo(photo=file_id, caption=caption, reply_markup=kb)
        else:
            await target.answer(caption, reply_markup=kb)
    except Exception:
        await target.answer(caption, reply_markup=kb)


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

    is_premium = user_service.is_premium(user)
    try:
        await cb.message.delete()
    except Exception:
        pass
    await _send_profile(cb.message, user, ref_count, fname or "", lang, is_premium)


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
