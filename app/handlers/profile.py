"""Profile screen — single message with photo + caption."""

from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from app.core.levels import get_required_xp
from app.db import get_session_maker
from app.keyboards import back_only
from app.keyboards.achievements import achievements_keyboard
from app.keyboards.profile import profile_keyboard
from app.utils.progress import build_progress_bar
from app.utils.timezone_flags import get_tz_display
from app.utils.safe_edit import safe_edit_or_send
from app.services import achievement_service, habit_log_service, referral_service, user_service
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

    flag, tz_label = get_tz_display(getattr(user, "timezone", None) or "Europe/Moscow")

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
            f"👋 Рады тебя видеть, {name} !\n\n"
            f"{flag} {tz_label}\n\n"
            f"💎 Подписка активна до: {premium_date}\n"
            f"🤝 Приглашено друзей: {ref_count}\n\n"
            f"⭐ Ваш уровень: {level}\n{progress}"
        )
    return (
        f"👋 Glad to see you, {name} !\n\n"
        f"{flag} {tz_label}\n\n"
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
    achievement_service.clear_achievements_screen(tid)
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


def _ach_page(c: str) -> int | None:
    if c and c.startswith("ach_page_"):
        try:
            return int(c.split("_")[-1])
        except (ValueError, IndexError):
            pass
    return None


@router.callback_query(lambda c: c.data == "profile_achievements" or (c.data and c.data.startswith("ach_page_")))
async def cb_profile_achievements(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    page = 0
    if cb.data and cb.data.startswith("ach_page_"):
        p = _ach_page(cb.data)
        if p is not None and p >= 0:
            page = p

    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code
        text = await achievement_service.build_achievements_header(session, user.id, lang)
        ach_list = await achievement_service.get_achievements_with_status(session, user.id, lang)

    kb = achievements_keyboard(ach_list, page, lang, len(ach_list))
    loc = await safe_edit_or_send(cb, text, reply_markup=kb)
    if loc:
        achievement_service.set_achievements_screen(tid, loc[0], loc[1])


@router.callback_query(lambda c: c.data and c.data.startswith("ach_view:"))
async def cb_ach_view(cb: CallbackQuery) -> None:
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        lang = user.language_code if user else "ru"
    await cb.answer(t(lang, "ach_unlocked_msg"))


@router.callback_query(lambda c: c.data and c.data.startswith("ach_lock:"))
async def cb_ach_lock(cb: CallbackQuery) -> None:
    aid = int(cb.data.split(":")[1])
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            await cb.answer()
            return
        lang = user.language_code
        ach = await achievement_service.get_achievement_by_id(session, aid)
        if not ach:
            await cb.answer()
            return
        desc = ach.description_ru if lang == "ru" else ach.description_en
        prefix = t(lang, "ach_locked_prefix")
        msg = f"{prefix} {desc}"
    await cb.answer(msg, show_alert=True)
