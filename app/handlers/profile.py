"""Profile screen."""

from datetime import date, datetime, timezone

from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select

from app.db import get_session_maker
from app.keyboards import back_only, main_menu, profile_keyboard
from app.models import HabitLog, User
from app.texts import t

router = Router(name="profile")


def _progress_bar(done: int, total: int) -> str:
    if total == 0:
        return "░░░░░░░░░░ 0%"
    pct = int(100 * done / total)
    filled = int(10 * done / total)
    return "█" * filled + "░" * (10 - filled) + f" {pct}%"


@router.callback_query(lambda c: c.data == "profile")
async def cb_profile(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code

        now = date.today()
        done_count = await session.scalar(
            select(func.count(HabitLog.id)).where(
                HabitLog.user_id == user.id,
                HabitLog.date >= now.replace(day=1),
                HabitLog.date <= now,
                HabitLog.status == "done",
            )
        ) or 0
        total_days = now.day
        bar = _progress_bar(done_count, total_days * 3)  # rough

        sub = "—" if not user.subscription_until else user.subscription_until.strftime("%d.%m.%Y")
        if user.subscription_until and user.subscription_until > datetime.now(timezone.utc):
            sub_status = f"✅ {sub}"
        else:
            sub_status = f"❌ {sub}"

        text = (
            f"{t(lang, 'profile_subscription')}: {sub_status}\n"
            f"{t(lang, 'profile_active')}: {done_count}\n"
            f"{t(lang, 'profile_progress')}: [{bar}]"
        )

    await cb.message.edit_text(text, reply_markup=profile_keyboard(lang))


@router.callback_query(lambda c: c.data == "profile_missed")
async def cb_missed(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    sm = get_session_maker()
    async with sm() as session:
        r = await session.execute(select(User).where(User.telegram_id == tid))
        user = r.scalar_one_or_none()
        if not user:
            return
        lang = user.language_code
        result = await session.execute(
            select(HabitLog).where(
                HabitLog.user_id == user.id,
                HabitLog.status == "skipped",
            ).order_by(HabitLog.date.desc()).limit(20)
        )
        logs = result.scalars().all()
    if not logs:
        text = t(lang, "profile_missed") + "\n\n" + ("Нет пропущенных" if lang == "ru" else "No missed habits.")
    else:
        lines = [f"{log.date} — {log.skip_reason or '—'}" for log in logs]
        text = t(lang, "profile_missed") + "\n\n" + "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=back_only(lang))

