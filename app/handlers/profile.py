"""Profile — Reply keyboard only."""

from datetime import date

from aiogram import Router, F
from aiogram.types import Message

from app.keyboards.reply import profile_menu, progress_menu, main_menu
from app.utils.i18n import format_date_short, get_month_name, reason_to_text

router = Router(name="profile")

PROGRESS_BTN = ("📊 Прогресс", "📊 Progress")
PROFILE_BUY = ("💳 Купить подписку", "💳 Buy subscription")
PROGRESS_MISSED = ("📋 Мои пропущенные привычки", "📋 My missed habits")
BTN_BACK = ("🔙 Back", "🔙 Назад")


def _progress_bar(success: int, total: int, length: int = 30) -> str:
    filled = int(round(length * success / total)) if total else 0
    return "█" * filled + "░" * (length - filled)


async def build_profile_content(user, t, session) -> tuple[str, type]:
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
    return text, profile_menu(t, bool(has_sub))


async def send_profile_screen(message: Message, user, t, session) -> None:
    text, kb = await build_profile_content(user, t, session)
    await message.answer(text, reply_markup=kb)


@router.message(F.text.in_(PROGRESS_BTN))
async def profile_progress_btn(message: Message, user, t, session) -> None:
    from app.services.progress_service import ProgressService

    now = date.today()
    progress_svc = ProgressService(session)
    success_count, total, days_list = await progress_svc.get_month_progress(user.id, now.year, now.month)
    lang = user.language if user.language in ("ru", "en") else "ru"
    month_name = get_month_name(lang, now.month)
    if total == 0 or not days_list:
        text = t("progress.title", month=month_name) + "\n\n" + t("progress.empty")
        has_missed = False
    else:
        bar = _progress_bar(success_count, total)
        text = t("progress.title", month=month_name) + "\n\n" + f"[{bar}]\n\n" + t("progress.days_done", count=success_count, total=total) + "\n\n"
        text += t("progress.no_skips") if success_count == total else t("progress.has_skips")
        missed = await progress_svc.get_missed_habits(user.id, now.year, now.month)
        has_missed = bool(missed)
    await message.answer(text, reply_markup=progress_menu(t, has_missed))


@router.message(F.text.in_(PROGRESS_MISSED))
async def profile_missed_btn(message: Message, user, t, session) -> None:
    from app.services.progress_service import ProgressService

    now = date.today()
    progress_svc = ProgressService(session)
    missed = await progress_svc.get_missed_habits(user.id, now.year, now.month)
    lang = user.language if user.language in ("ru", "en") else "ru"
    if not missed:
        text = t("progress.empty")
    else:
        lines = [f"{format_date_short(lang, d)} — {title} ({reason_to_text(lang, reason)})" for d, title, reason in missed]
        text = t("progress.my_missed") + "\n\n" + "\n".join(lines)
    await message.answer(text, reply_markup=progress_menu(t, False))


@router.message(F.text.in_(PROFILE_BUY))
async def profile_buy_btn(message: Message, t) -> None:
    from app.handlers.subscription import send_tariff_screen
    await send_tariff_screen(message, t)
