"""
Profile and settings handlers.
"""

import random
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.fsm.context_data import FSM_SETTINGS_REGION
from app.fsm.states import SettingsFSM
from app.keyboards.profile import (
    detail_progress_keyboard,
    profile_keyboard,
    settings_keyboard,
    timezone_list_keyboard,
    timezone_method_keyboard,
    timezone_region_keyboard,
)
from app.keyboards.main_menu import main_menu_keyboard
from app.services.insights_service import InsightsService
from app.services.profile_service import ProfileService
from app.texts import (
    DETAIL_PROGRESS_LEGEND,
    DETAIL_PROGRESS_TITLE,
    PROFILE_HEADER,
    PROFILE_PROGRESS_BLOCK,
    PROFILE_QUOTES,
    SETTINGS_NOTIFICATIONS_OFF,
    SETTINGS_NOTIFICATIONS_ON,
    SETTINGS_TITLE,
    TIMEZONE_CHOOSE,
    TIMEZONE_INVALID,
    TIMEZONE_MANUAL_PROMPT,
    TIMEZONE_SAVED,
)
from app.utils.message_lifecycle import send_screen_from_event
from app.utils.timezone import format_timezone_display, validate_timezone

router = Router(name="profile")

BAR_LENGTH = 10


def _pick_quote(last_index: int | None) -> tuple[str, int]:
    """Pick random quote, avoiding repeat of last one."""
    indices = list(range(len(PROFILE_QUOTES)))
    if last_index is not None and len(indices) > 1:
        indices = [i for i in indices if i != last_index]
    idx = random.choice(indices)
    return PROFILE_QUOTES[idx], idx


def _progress_bar(pct: float) -> str:
    """Text progress bar: ████████░░ 72%"""
    filled = round(BAR_LENGTH * pct / 100) if pct else 0
    filled = min(filled, BAR_LENGTH)
    return "█" * filled + "░" * (BAR_LENGTH - filled) + f" {round(pct)}%"


def _build_profile_text(profile_data, name: str, quote: str) -> str:
    """Build full profile message."""
    header = PROFILE_HEADER.format(name=name, quote=quote)
    bar = _progress_bar(profile_data.completion_rate_pct)
    block = PROFILE_PROGRESS_BLOCK.format(
        progress_bar=bar,
        streak=profile_data.streak_days,
        completed=profile_data.completed_habits,
        skipped=profile_data.skipped_habits,
        completed_7d=profile_data.completed_7d,
        skipped_7d=profile_data.skipped_7d,
        insight=profile_data.insight,
        status=profile_data.status,
        referrals=profile_data.referral_count,
        timezone=profile_data.timezone_display,
        subscription=profile_data.subscription_text,
    )
    return f"{header}\n\n{block}"


# --- Profile (STICKY — не удаляется) ---

@router.message(F.text == "📊 Мой профиль")
async def profile_handler(message: Message, user, session) -> None:
    """Show profile screen — STICKY."""
    if hasattr(user, "profile_views_count"):
        user.profile_views_count = getattr(user, "profile_views_count", 0) + 1
        await session.flush()

    from app.services.achievement_service import AchievementService
    from app.services.retention_paywall_service import RetentionPaywallService

    ach_svc = AchievementService(session)
    new_ach = await ach_svc.check_and_unlock(user)
    if new_ach:
        from app.keyboards.profile import achievement_reward_keyboard
        from app.texts import ACHIEVEMENT_NEW_TITLE, ACHIEVEMENT_REWARD
        reward_text = f"{ACHIEVEMENT_NEW_TITLE}\n\n{ACHIEVEMENT_REWARD.format(icon=new_ach.icon, title=new_ach.title, description=new_ach.description)}"
        await send_screen_from_event(
            message, user.id, reward_text,
            reply_markup=achievement_reward_keyboard(),
        )
        return

    paywall_svc = RetentionPaywallService(session)
    should_paywall, pay_key = await paywall_svc.should_show_paywall(user)
    if should_paywall and pay_key:
        from app.keyboards.profile import paywall_keyboard
        paywall_text = {
            "profile_5": "🔥 Ты отлично идёшь!\nЗакрепи результат с Premium — привычки любят стабильность.",
            "achievements_2": "🏆 Два достижения — ты на волне! Premium откроет все награды.",
            "streak_5": "🔥 Пять дней подряд — невероятно! Premium поможет сохранять серии.",
            "trial_ending": "⏰ Триал заканчивается. Оформи Premium и продолжай без ограничений.",
        }.get(pay_key, "💎 Premium открывает больше возможностей.")
        if hasattr(user, "last_paywall_shown_at"):
            user.last_paywall_shown_at = datetime.now(timezone.utc)
            await session.flush()
        await send_screen_from_event(
            message, user.id, paywall_text,
            reply_markup=paywall_keyboard(),
        )
        return

    tz_display = format_timezone_display(user.timezone)
    insights_svc = InsightsService(session)
    insight_text, insight_id = await insights_svc.get_insight_for_profile(
        user.id,
        getattr(user, "last_insight_id", None),
        getattr(user, "last_insight_at", None),
    )
    if hasattr(user, "last_insight_id"):
        user.last_insight_id = insight_id
        user.last_insight_at = datetime.now(timezone.utc)
        await session.flush()

    svc = ProfileService(session)
    profile_data = await svc.get_profile_data(user.id, tz_display, insight_text)
    quote, quote_idx = _pick_quote(getattr(user, "last_profile_quote_index", None))
    if hasattr(user, "last_profile_quote_index"):
        user.last_profile_quote_index = quote_idx
        await session.flush()

    name = user.first_name or "друг"
    text = _build_profile_text(profile_data, name, quote)
    await send_screen_from_event(
        message, user.id, text,
        reply_markup=profile_keyboard(),
        sticky=True,
    )


@router.callback_query(F.data == "profile_habits")
async def profile_habits_cb(callback: CallbackQuery, user, session) -> None:
    """Navigate to habits from profile."""
    await callback.answer()
    from app.keyboards.habits import habits_list_keyboard
    from app.repositories.habit_repo import HabitRepository
    from app.texts import HABITS_EMPTY, HABITS_LIST_TITLE

    repo = HabitRepository(session)
    habits = await repo.get_user_habits(user.id)
    if not habits:
        await send_screen_from_event(callback, user.id, HABITS_EMPTY)
    else:
        await send_screen_from_event(
            callback, user.id, HABITS_LIST_TITLE,
            reply_markup=habits_list_keyboard(habits),
        )


@router.callback_query(F.data == "profile_invite")
async def profile_invite_cb(callback: CallbackQuery, user) -> None:
    """Referral link from profile — STICKY."""
    await callback.answer()
    bot = callback.bot
    me = await bot.me()
    username = me.username if me else "your_bot"
    link = f"https://t.me/{username}?start=ref_{user.referral_code}" if user.referral_code else "—"
    from app.texts import REFERRAL_INTRO
    await send_screen_from_event(
        callback, user.id, REFERRAL_INTRO.format(link=link), sticky=True
    )


@router.callback_query(F.data == "profile_detail_progress")
async def profile_detail_progress_cb(callback: CallbackQuery, user, session) -> None:
    """Detail progress view (14-day by weekday). Free users see blocker."""
    from app.config.constants import UserTier

    await callback.answer()
    if user.tier != UserTier.PREMIUM:
        from app.keyboards.profile import progress_blocker_keyboard
        from app.texts import PROGRESS_BLOCKER
        await send_screen_from_event(
            callback, user.id,
            f"📈 Прогресс: ███████░░░ 70%\n{PROGRESS_BLOCKER}",
            reply_markup=progress_blocker_keyboard(),
        )
        return
    svc = ProfileService(session)
    data = await svc.get_detail_progress(user.id, days=14)
    lines = [DETAIL_PROGRESS_TITLE.format(days=14)]
    for label, bar in data["bars"].items():
        lines.append(f"{label}  {bar}")
    lines.append(DETAIL_PROGRESS_LEGEND.format(
        best_day=data["best_day"], best_time=data["best_time"]
    ))
    text = "\n".join(lines)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=detail_progress_keyboard(),
    )


@router.callback_query(F.data == "detail_progress_back")
async def detail_progress_back_cb(callback: CallbackQuery, user, session) -> None:
    """Back from detail progress to profile."""
    await callback.answer()
    tz_display = format_timezone_display(user.timezone)
    insights_svc = InsightsService(session)
    insight_text, _ = await insights_svc.get_insight_for_profile(
        user.id, getattr(user, "last_insight_id", None), getattr(user, "last_insight_at", None)
    )
    svc = ProfileService(session)
    profile_data = await svc.get_profile_data(user.id, tz_display, insight_text)
    quote, _ = _pick_quote(getattr(user, "last_profile_quote_index", None))
    name = user.first_name or "друг"
    text = _build_profile_text(profile_data, name, quote)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=profile_keyboard(),
        sticky=True,
    )


@router.callback_query(F.data == "profile_subscription")
async def profile_subscription_cb(callback: CallbackQuery, user) -> None:
    """Navigate to balance/subscription."""
    await callback.answer()
    await send_screen_from_event(
        callback, user.id,
        "Перейди в «💳 Баланс» для управления подпиской.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "profile_settings")
async def profile_settings_cb(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Show settings from profile."""
    await callback.answer()
    await state.clear()
    tz_display = format_timezone_display(user.timezone)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = SETTINGS_TITLE.format(timezone=tz_display, notifications=notif)
    await send_screen_from_event(callback, user.id, text, reply_markup=settings_keyboard())


# --- Settings (from main menu) ---

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message, user, state: FSMContext) -> None:
    """Settings screen."""
    await state.clear()
    tz_display = format_timezone_display(user.timezone)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = SETTINGS_TITLE.format(timezone=tz_display, notifications=notif)
    await send_screen_from_event(message, user.id, text, reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings_back")
async def settings_back_cb(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Back from settings to main menu."""
    await callback.answer()
    await state.clear()
    await send_screen_from_event(
        callback, user.id, "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "settings_notifications")
async def settings_notifications_cb(callback: CallbackQuery, user, session) -> None:
    """Toggle notifications."""
    await callback.answer()
    user.notifications_enabled = not user.notifications_enabled
    await session.flush()
    tz_display = format_timezone_display(user.timezone)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = SETTINGS_TITLE.format(timezone=tz_display, notifications=notif)
    await callback.message.edit_text(text, reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings_timezone")
async def settings_timezone_cb(callback: CallbackQuery, state: FSMContext) -> None:
    """Start timezone selection."""
    await callback.answer()
    await state.set_state(SettingsFSM.choosing_timezone_method)
    await callback.message.answer(TIMEZONE_CHOOSE, reply_markup=timezone_method_keyboard())


# --- Timezone FSM ---

@router.callback_query(F.data == "tz_back", SettingsFSM.choosing_timezone_method)
@router.callback_query(F.data == "tz_back", SettingsFSM.choosing_region)
@router.callback_query(F.data == "tz_region_back", SettingsFSM.choosing_timezone_from_list)
async def tz_back_cb(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Back in timezone flow."""
    await callback.answer()
    await state.clear()
    tz_display = format_timezone_display(user.timezone)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = SETTINGS_TITLE.format(timezone=tz_display, notifications=notif)
    await send_screen_from_event(callback, user.id, text, reply_markup=settings_keyboard())


@router.callback_query(F.data.startswith("tz_method:"), SettingsFSM.choosing_timezone_method)
async def tz_method_cb(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Region or manual."""
    await callback.answer()
    method = callback.data.split(":")[1]
    if method == "region":
        await state.set_state(SettingsFSM.choosing_region)
        await send_screen_from_event(
            callback, user.id, "Выбери регион:",
            reply_markup=timezone_region_keyboard(),
        )
    else:
        await state.set_state(SettingsFSM.waiting_timezone_input)
        await send_screen_from_event(callback, user.id, TIMEZONE_MANUAL_PROMPT)


@router.callback_query(F.data.startswith("tz_region:"), SettingsFSM.choosing_region)
async def tz_region_cb(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Show timezone list for region."""
    await callback.answer()
    region_id = callback.data.split(":")[1]
    await state.update_data(**{FSM_SETTINGS_REGION: region_id})
    await state.set_state(SettingsFSM.choosing_timezone_from_list)
    kb = timezone_list_keyboard(region_id, selected_tz=user.timezone)
    await send_screen_from_event(
        callback, user.id, "Выбери часовой пояс:",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("tz_select:"), SettingsFSM.choosing_timezone_from_list)
async def tz_select_cb(callback: CallbackQuery, user, session, state: FSMContext) -> None:
    """Save selected timezone."""
    tz_name = callback.data.split(":", 1)[1]
    if not validate_timezone(tz_name):
        await callback.answer(TIMEZONE_INVALID, show_alert=True)
        return
    await callback.answer()
    user.timezone = tz_name
    await session.flush()
    await state.clear()
    tz_display = format_timezone_display(tz_name)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = TIMEZONE_SAVED.format(timezone=tz_display) + "\n\n" + SETTINGS_TITLE.format(
        timezone=tz_display, notifications=notif
    )
    await send_screen_from_event(callback, user.id, text, reply_markup=settings_keyboard())


@router.message(SettingsFSM.waiting_timezone_input, F.text)
async def tz_input_msg(message: Message, user, session, state: FSMContext) -> None:
    """Manual timezone input."""
    tz_name = message.text.strip()
    validated = validate_timezone(tz_name)
    if not validated:
        await send_screen_from_event(message, user.id, TIMEZONE_INVALID)
        return
    user.timezone = validated
    await session.flush()
    await state.clear()
    tz_display = format_timezone_display(validated)
    notif = SETTINGS_NOTIFICATIONS_ON if user.notifications_enabled else SETTINGS_NOTIFICATIONS_OFF
    text = TIMEZONE_SAVED.format(timezone=tz_display) + "\n\n" + SETTINGS_TITLE.format(
        timezone=tz_display, notifications=notif
    )
    await send_screen_from_event(message, user.id, text, reply_markup=settings_keyboard())
