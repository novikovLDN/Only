"""Achievement check and unlock logic."""

import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Achievement, User, UserAchievement
from app.services import metrics_service, referral_service

logger = logging.getLogger(__name__)

CONDITIONS = {
    "FIRST_STEP": lambda m: m["habits_created"] >= 1,
    "AWARE_START": lambda m: m["habits_created"] >= 3,
    "DAY_ARCHITECT": lambda m: m["habits_created"] >= 5,
    "FULL_CONTROL": lambda m: m.get("profile_completed", False) and m.get("reminders_configured", False),
    "FIRST_MARK": lambda m: m["completed_total"] >= 1,
    "ACCELERATION": lambda m: m["completed_total"] >= 5,
    "FIRST_10": lambda m: m["completed_total"] >= 10,
    "WEEK_FOCUS": lambda m: m.get("all_habits_one_day", False) and m.get("completed_one_day", 0) > 0,
    "PERFECT_MONDAY": lambda m: m.get("all_habits_monday", False),
    "NO_SKIP_3": lambda m: m.get("no_skips_days", 0) >= 3,
    "STREAK_7": lambda m: m["streak_days"] >= 7,
    "STREAK_14": lambda m: m["streak_days"] >= 14,
    "STREAK_21": lambda m: m["streak_days"] >= 21,
    "STREAK_30": lambda m: m["streak_days"] >= 30,
    "STREAK_45": lambda m: m["streak_days"] >= 45,
    "STREAK_60": lambda m: m["streak_days"] >= 60,
    "STREAK_90": lambda m: m["streak_days"] >= 90,
    "STREAK_180": lambda m: m["streak_days"] >= 180,
    "STREAK_365": lambda m: m["streak_days"] >= 365,
    "PHOENIX": lambda m: m.get("returned_after_skip_days", 0) >= 5,
    "PERFECT_DAY": lambda m: m.get("perfect_day_count", 0) >= 1,
    "PERFECT_7": lambda m: m.get("perfect_streak", 0) >= 7,
    "PERFECT_WEEK": lambda m: m.get("all_habits_7_days", False),
    "PERFECT_14": lambda m: m.get("perfect_streak", 0) >= 14,
    "PERFECT_MONTH": lambda m: m.get("perfect_streak", 0) >= 30,
    "ABSOLUTE": lambda m: m.get("perfect_weeks_in_month", 0) >= 3,
    "MAXIMALIST": lambda m: m.get("perfect_streak", 0) >= 10,
    "MARK_50": lambda m: m["completed_total"] >= 50,
    "MARK_100": lambda m: m["completed_total"] >= 100,
    "MARK_250": lambda m: m["completed_total"] >= 250,
    "MARK_500": lambda m: m["completed_total"] >= 500,
    "MARK_1000": lambda m: m["completed_total"] >= 1000,
    "SUPERACTIVE": lambda m: m.get("completed_one_day", 0) >= 20,
    "STRONG_WEEK": lambda m: m.get("completed_7_days", 0) >= 70,
    "PRODUCTIVE_MONTH": lambda m: m.get("completed_month", 0) >= 300,
    "FLEXIBLE": lambda m: m.get("habit_changed_streak_ok", False),
    "GROWTH": lambda m: m.get("habit_goal_increased", False),
    "MULTIFOCUS": lambda m: m.get("five_habits_14_days", False),
    "BALANCE": lambda m: m.get("three_categories_30_days", False),
    "EXPERIMENTER": lambda m: m.get("new_habit_7_days", False),
    "FIRST_FRIEND": lambda m: m["referrals_count"] >= 1,
    "TEAM_START": lambda m: m["referrals_count"] >= 3,
    "AMBASSADOR": lambda m: m["referrals_count"] >= 10,
    "SUPPORTER_1M": lambda m: m["subscription_months"] >= 1,
    "CHOICE_3M": lambda m: m["subscription_months"] >= 3,
    "PLAN_6M": lambda m: m["subscription_months"] >= 6,
    "INVESTOR_12M": lambda m: m["subscription_months"] >= 12,
    "TEAM_DISCIPLINE": lambda m: m.get("referrals_streak_7", 0) >= 3,
    "SOCIAL_DRIVE": lambda m: m.get("synced_with_friend_14", False),
    "LEADER": lambda m: m.get("referrals_active_30", 0) >= 5,
}


async def _get_metrics(session: AsyncSession, user_id: int, user: User | None) -> dict:
    """Get metrics from user_metrics (after recalc) or fallback minimal dict."""
    try:
        await metrics_service.recalculate_user_metrics(session, user_id, user)
        m = await metrics_service.get_or_create_metrics(session, user_id)
        await session.refresh(m)
        return metrics_service.metrics_to_dict(m, user)
    except Exception as e:
        logger.warning("Metrics recalc failed, using fallback: %s", e)
    referrals = await referral_service.count_referrals(session, user_id)
    sub_months = 0
    if user and user.premium_until:
        pu = user.premium_until
        if pu.tzinfo is None:
            pu = pu.replace(tzinfo=timezone.utc)
        if pu > datetime.now(timezone.utc):
            sub_months = max(1, (pu - datetime.now(timezone.utc)).days // 30)
    return {
        "habits_created": 0,
        "completed_total": 0,
        "streak_days": 0,
        "referrals_count": referrals,
        "subscription_months": sub_months,
        "profile_completed": bool(user and user.timezone and user.timezone != "UTC"),
        "reminders_configured": False,
        "all_habits_one_day": False,
        "all_habits_monday": False,
        "no_skips_days": 0,
        "returned_after_skip_days": 0,
        "perfect_day_count": 0,
        "perfect_streak": 0,
        "all_habits_7_days": False,
        "perfect_weeks_in_month": 0,
        "completed_one_day": 0,
        "completed_7_days": 0,
        "completed_month": 0,
        "habit_changed_streak_ok": False,
        "habit_goal_increased": False,
        "five_habits_14_days": False,
        "three_categories_30_days": False,
        "new_habit_7_days": False,
        "referrals_streak_7": 0,
        "synced_with_friend_14": False,
        "referrals_active_30": 0,
    }


async def _get_unlocked_ids(session: AsyncSession, user_id: int) -> set[int]:
    r = await session.execute(
        select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
    )
    return set(row[0] for row in r.all())


async def check_achievements(
    session: AsyncSession,
    user_id: int,
    user: User | None,
    bot: Bot | None,
    telegram_id: int | None = None,
) -> list[Achievement]:
    """Check and unlock achievements. Returns newly unlocked achievements."""
    result = await session.execute(select(Achievement))
    all_achievements = {a.code: a for a in result.scalars().unique().all()}
    unlocked_ids = await _get_unlocked_ids(session, user_id)
    metrics = await _get_metrics(session, user_id, user)
    newly_unlocked: list[Achievement] = []

    for code, cond_fn in CONDITIONS.items():
        ach = all_achievements.get(code)
        if not ach or ach.id in unlocked_ids:
            continue
        try:
            if cond_fn(metrics):
                ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
                session.add(ua)
                await session.flush()
                newly_unlocked.append(ach)
                if code == "FLEXIBLE":
                    await metrics_service.reset_flexibility_flags(session, user_id)
                elif code == "GROWTH":
                    await metrics_service.reset_growth_flag(session, user_id)
                if bot and telegram_id:
                    lang = (user.language_code or "ru")[:2].lower()
                    lang = "en" if lang == "en" else "ru"
                    msg = ach.unlock_msg_ru if lang == "ru" else ach.unlock_msg_en
                    name = ach.name_ru if lang == "ru" else ach.name_en
                    try:
                        await bot.send_message(
                            telegram_id,
                            f"🏆 {name}\n\n{msg}",
                        )
                    except Exception as e:
                        logger.warning("Failed to send achievement unlock: %s", e)
        except Exception as e:
            logger.warning("Achievement %s check failed: %s", code, e)

    return newly_unlocked


async def get_achievements_with_status(
    session: AsyncSession,
    user_id: int,
    lang: str,
) -> list[tuple[int, str, bool]]:
    """Return list of (achievement_id, display_name, unlocked) ordered by id."""
    result = await session.execute(select(Achievement).order_by(Achievement.id))
    all_ach = result.scalars().unique().all()
    unlocked = await _get_unlocked_ids(session, user_id)
    lang = "en" if (lang or "").lower() == "en" else "ru"
    return [
        (a.id, a.name_ru if lang == "ru" else a.name_en, a.id in unlocked)
        for a in all_ach
    ]


async def get_achievement_by_id(
    session: AsyncSession,
    achievement_id: int,
) -> Achievement | None:
    return await session.get(Achievement, achievement_id)
