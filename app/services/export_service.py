"""Data export service — GDPR compliance."""

import json
import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Habit, HabitLog, HabitTime, Payment, Referral, User, UserAchievement, Achievement

logger = logging.getLogger(__name__)


def _serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def export_user_data(session: AsyncSession, user: User) -> str:
    """Export all user data as JSON string (GDPR data portability).

    Returns a JSON string with all user data.
    """
    # User profile
    profile = {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "username": user.username,
        "language_code": user.language_code,
        "timezone": user.timezone,
        "xp": user.xp,
        "level": user.level,
        "premium_until": user.premium_until,
        "created_at": user.created_at,
    }

    # Habits
    habits_result = await session.execute(
        select(Habit).where(Habit.user_id == user.id)
    )
    habits = []
    for habit in habits_result.scalars().all():
        times_result = await session.execute(
            select(HabitTime).where(HabitTime.habit_id == habit.id)
        )
        times = [
            {"weekday": ht.weekday, "time": str(ht.time)}
            for ht in times_result.scalars().all()
        ]
        habits.append({
            "id": habit.id,
            "title": habit.title,
            "is_active": habit.is_active,
            "created_at": habit.created_at,
            "schedule": times,
        })

    # Habit logs
    logs_result = await session.execute(
        select(HabitLog).where(HabitLog.user_id == user.id).order_by(HabitLog.log_date.desc())
    )
    logs = [
        {
            "habit_id": log.habit_id,
            "date": log.log_date,
            "status": log.status,
        }
        for log in logs_result.scalars().all()
    ]

    # Payments (sanitized — no crypto addresses)
    payments_result = await session.execute(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc())
    )
    payments = [
        {
            "tariff": p.tariff,
            "amount_kopecks": p.amount,
            "provider": p.provider,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in payments_result.scalars().all()
    ]

    # Achievements
    ach_result = await session.execute(
        select(UserAchievement, Achievement)
        .join(Achievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user.id)
    )
    achievements = [
        {
            "achievement": ach.name_en or ach.name_ru,
            "unlocked_at": ua.unlocked_at,
        }
        for ua, ach in ach_result.all()
    ]

    # Referrals
    refs_result = await session.execute(
        select(Referral).where(Referral.referrer_id == user.id)
    )
    referrals_sent = [
        {"referral_user_id": r.referral_user_id, "reward_given": r.reward_given, "created_at": r.created_at}
        for r in refs_result.scalars().all()
    ]

    export = {
        "export_date": datetime.utcnow().isoformat(),
        "profile": profile,
        "habits": habits,
        "habit_logs": logs,
        "payments": payments,
        "achievements": achievements,
        "referrals_sent": referrals_sent,
    }

    return json.dumps(export, default=_serialize_datetime, ensure_ascii=False, indent=2)
