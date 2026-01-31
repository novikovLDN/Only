"""
Achievements and Calendar handlers.
"""

from calendar import monthrange
from datetime import date, datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.repositories.achievement_repo import AchievementRepository

from app.config.constants import UserTier
from app.keyboards.profile import (
    achievement_premium_keyboard,
    achievement_reward_keyboard,
    achievements_keyboard,
    calendar_day_keyboard,
    calendar_keyboard,
    detail_progress_keyboard,
    paywall_keyboard,
    progress_blocker_keyboard,
    profile_keyboard,
)
from app.services.achievement_service import AchievementService
from app.services.profile_service import ProfileService
from app.services.retention_paywall_service import RetentionPaywallService
from app.texts import (
    ACHIEVEMENTS_LEGEND,
    ACHIEVEMENTS_TITLE,
    ACHIEVEMENT_PREMIUM_LOCKED,
    ACHIEVEMENT_REWARD,
    CALENDAR_DAY_EMPTY,
    CALENDAR_DAY_TITLE,
    CALENDAR_LEGEND,
    CALENDAR_TITLE,
    MONTH_NAMES,
    MONTH_NAMES_NOM,
    PAYWALL_PROFILE_5,
    PAYWALL_ACHIEVEMENTS_2,
    PAYWALL_STREAK_5,
    PAYWALL_TRIAL_ENDING,
    PROGRESS_BLOCKER,
    STREAK_LOST_FREE,
)
from app.utils.message_lifecycle import send_screen_from_event

router = Router(name="achievements")


# --- Achievements ---

@router.callback_query(F.data == "profile_achievements")
async def achievements_list_cb(callback: CallbackQuery, user, session) -> None:
    """Achievements list."""
    await callback.answer()
    repo = AchievementRepository(session)
    achievements = await repo.get_all()
    unlocked = await repo.get_unlocked_ids(user.id)
    is_premium = user.tier == UserTier.PREMIUM

    lines = [ACHIEVEMENTS_TITLE, ""]
    for a in achievements:
        status = "✅" if a.id in unlocked else ("🔒" if a.is_premium and not is_premium else "🔒")
        lines.append(f"{a.icon} {a.title} {status}")
    lines.append(ACHIEVEMENTS_LEGEND)
    text = "\n".join(lines)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=achievements_keyboard(achievements, unlocked, is_premium),
    )


@router.callback_query(F.data.startswith("ach_lock:"))
async def achievement_lock_cb(callback: CallbackQuery, user) -> None:
    """Clicked on locked premium achievement."""
    await callback.answer()
    await send_screen_from_event(
        callback, user.id, ACHIEVEMENT_PREMIUM_LOCKED,
        reply_markup=achievement_premium_keyboard(),
    )


@router.callback_query(F.data == "ach:noop")
async def ach_noop_cb(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "achievement_reward_ok")
async def achievement_reward_ok_cb(callback: CallbackQuery, user, session) -> None:
    """From reward screen to achievements list."""
    await callback.answer()
    repo = AchievementRepository(session)
    achievements = await repo.get_all()
    unlocked = await repo.get_unlocked_ids(user.id)
    is_premium = user.tier == UserTier.PREMIUM

    lines = [ACHIEVEMENTS_TITLE, ""]
    for a in achievements:
        status = "✅" if a.id in unlocked else ("🔒" if a.is_premium and not is_premium else "🔒")
        lines.append(f"{a.icon} {a.title} {status}")
    lines.append(ACHIEVEMENTS_LEGEND)
    text = "\n".join(lines)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=achievements_keyboard(achievements, unlocked, is_premium),
    )


@router.callback_query(F.data == "achievements_back")
async def achievements_back_cb(callback: CallbackQuery, user, session) -> None:
    """Back to profile."""
    await callback.answer()
    from app.services.insights_service import InsightsService
    from app.utils.timezone import format_timezone_display

    tz_display = format_timezone_display(user.timezone)
    insights_svc = InsightsService(session)
    insight_text, _ = await insights_svc.get_insight_for_profile(
        user.id, getattr(user, "last_insight_id", None), getattr(user, "last_insight_at", None)
    )
    svc = ProfileService(session)
    profile_data = await svc.get_profile_data(user.id, tz_display, insight_text)
    from app.handlers.profile import _build_profile_text, _pick_quote
    quote, _ = _pick_quote(getattr(user, "last_profile_quote_index", None))
    name = user.first_name or "друг"
    text = _build_profile_text(profile_data, name, quote)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=profile_keyboard(),
        sticky=True,
    )


# --- Calendar ---

def _build_calendar_grid(user_id: int, habit_repo, year: int, month: int) -> str:
    """Build calendar grid for month. Returns multiline string."""
    first_day, num_days = monthrange(year, month)
    week_start = (first_day - 6) % 7
    grid = []
    header = "Пн Вт Ср Чт Пт Сб Вс"
    grid.append(header)
    row = [" "] * 7
    for d in range(1, num_days + 1):
        idx = (week_start + d - 1) % 7
        cell_date = date(year, month, d)
        status = habit_repo.get_day_calendar_status(user_id, cell_date)
        if status == "all":
            ch = "█"
        elif status == "partial":
            ch = "░"
        else:
            ch = "•"
        row[idx] = ch
        if idx == 6 or d == num_days:
            grid.append("  ".join(row))
            row = [" "] * 7
    return "\n".join(grid)


@router.callback_query(F.data.startswith("cal:"))
async def calendar_month_cb(callback: CallbackQuery, user, session) -> None:
    """Calendar month view."""
    await callback.answer()
    parts = callback.data.split(":")
    year, month = int(parts[1]), int(parts[2])
    from app.repositories.habit_repo import HabitRepository

    repo = HabitRepository(session)
    grid = await _build_calendar_grid_async(user.id, repo, year, month)
    title = CALENDAR_TITLE.format(month=MONTH_NAMES_NOM[month], year=year)
    text = f"{title}\n\n{grid}\n{CALENDAR_LEGEND}"
    kb = calendar_keyboard(year, month)
    await send_screen_from_event(callback, user.id, text, reply_markup=kb)


async def _build_calendar_grid_async(user_id: int, habit_repo, year: int, month: int) -> str:
    first_day, num_days = monthrange(year, month)
    week_start = (first_day - 6) % 7
    grid = []
    grid.append("Пн Вт Ср Чт Пт Сб Вс")
    row = [" "] * 7
    for d in range(1, num_days + 1):
        idx = (week_start + d - 1) % 7
        cell_date = date(year, month, d)
        status = await habit_repo.get_day_calendar_status(user_id, cell_date)
        if status == "all":
            ch = "█"
        elif status == "partial":
            ch = "░"
        else:
            ch = "•"
        row[idx] = ch
        if idx == 6 or d == num_days:
            grid.append("  ".join(row))
            row = [" "] * 7
    return "\n".join(grid)


@router.callback_query(F.data == "profile_calendar")
async def calendar_open_cb(callback: CallbackQuery, user, session) -> None:
    """Open calendar (current month)."""
    await callback.answer()
    now = date.today()
    from app.repositories.habit_repo import HabitRepository

    repo = HabitRepository(session)
    grid = await _build_calendar_grid_async(user.id, repo, now.year, now.month)
    title = CALENDAR_TITLE.format(month=MONTH_NAMES_NOM[now.month], year=now.year)
    text = f"{title}\n\n{grid}\n{CALENDAR_LEGEND}"
    kb = calendar_keyboard(now.year, now.month)
    await send_screen_from_event(callback, user.id, text, reply_markup=kb)


@router.callback_query(F.data == "cal:noop")
async def cal_noop_cb(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("calday:"))
async def calendar_day_cb(callback: CallbackQuery, user, session) -> None:
    """Day detail."""
    await callback.answer()
    parts = callback.data.split(":")
    year, month, day = int(parts[1]), int(parts[2]), int(parts[3])
    d = date(year, month, day)
    from app.repositories.habit_repo import HabitRepository

    repo = HabitRepository(session)
    logs = await repo.get_day_habit_logs(user.id, d)
    title = CALENDAR_DAY_TITLE.format(day=day, month=MONTH_NAMES[month], year=year)
    if not logs:
        text = f"{title}\n\n{CALENDAR_DAY_EMPTY}"
    else:
        lines = [title, ""]
        for name, completed in logs:
            lines.append(f"{'✔️' if completed else '❌'} {name}")
        text = "\n".join(lines)
    kb = calendar_day_keyboard(year, month)
    await send_screen_from_event(callback, user.id, text, reply_markup=kb)


@router.callback_query(F.data == "paywall_later")
async def paywall_later_cb(callback: CallbackQuery, user, session) -> None:
    """User clicked 'Позже' on paywall — back to profile."""
    await callback.answer()
    from app.services.insights_service import InsightsService
    from app.utils.timezone import format_timezone_display

    tz_display = format_timezone_display(user.timezone)
    insights_svc = InsightsService(session)
    insight_text, _ = await insights_svc.get_insight_for_profile(
        user.id, getattr(user, "last_insight_id", None), getattr(user, "last_insight_at", None)
    )
    svc = ProfileService(session)
    profile_data = await svc.get_profile_data(user.id, tz_display, insight_text)
    from app.handlers.profile import _build_profile_text, _pick_quote
    quote, _ = _pick_quote(getattr(user, "last_profile_quote_index", None))
    name = user.first_name or "друг"
    text = _build_profile_text(profile_data, name, quote)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=profile_keyboard(),
        sticky=True,
    )


@router.callback_query(F.data == "calendar_back")
async def calendar_back_cb(callback: CallbackQuery, user, session) -> None:
    """Back to profile from calendar."""
    await callback.answer()
    from app.services.insights_service import InsightsService
    from app.utils.timezone import format_timezone_display

    tz_display = format_timezone_display(user.timezone)
    insights_svc = InsightsService(session)
    insight_text, _ = await insights_svc.get_insight_for_profile(
        user.id, getattr(user, "last_insight_id", None), getattr(user, "last_insight_at", None)
    )
    svc = ProfileService(session)
    profile_data = await svc.get_profile_data(user.id, tz_display, insight_text)
    from app.handlers.profile import _build_profile_text, _pick_quote
    quote, _ = _pick_quote(getattr(user, "last_profile_quote_index", None))
    name = user.first_name or "друг"
    text = _build_profile_text(profile_data, name, quote)
    await send_screen_from_event(
        callback, user.id, text,
        reply_markup=profile_keyboard(),
        sticky=True,
    )
