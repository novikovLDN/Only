"""
Notification jobs implementation.
"""

from datetime import datetime, date, timedelta

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.base import get_async_session_maker
from app.models.user import User
from app.models.habit import Habit
from app.models.habit_schedule import HabitSchedule
from app.models.subscription import Subscription
from app.services.notification_service import NotificationService
from app.utils.timezone import to_user_tz, utc_now


async def run_habit_reminders(bot: Bot) -> None:
    """Check and send habit reminders (timezone-aware)."""
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        now_utc = utc_now()
        # Get all active schedules
        result = await session.execute(
            select(HabitSchedule, Habit, User)
            .join(Habit, Habit.id == HabitSchedule.habit_id)
            .join(User, User.id == Habit.user_id)
            .where(HabitSchedule.is_enabled == True)
            .where(Habit.is_active == True)
        )
        rows = result.all()
        notifier = NotificationService(bot)
        for sched, habit, user in rows:
            try:
                user_now = to_user_tz(now_utc, user.timezone)
                target_time = sched.reminder_time  # HH:MM
                h, m = map(int, target_time.split(":"))
                if user_now.hour == h and user_now.minute < 5:  # Within 5-min window
                    from app.keyboards.main_menu import habit_reminder_keyboard

                    await notifier.send_habit_reminder(
                        user, habit, habit_reminder_keyboard(habit.id)
                    )
            except Exception:
                pass  # Log but don't fail job


async def run_trial_notifications(bot: Bot) -> None:
    """Trial lifecycle: +36h, +90h, -24h, -3h, expired."""
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(User).where(User.tier == "trial").where(User.trial_ends_at.isnot(None))
        )
        users = result.scalars().all()
        notifier = NotificationService(bot)
        for user in users:
            if not user.trial_ends_at:
                continue
            delta = (user.trial_ends_at - now).total_seconds() / 3600
            msg_type = None
            if delta <= 0:
                msg_type = "trial_expired"
            elif 0 < delta <= 3:
                msg_type = "trial_minus_3h"
            elif 3 < delta <= 24:
                msg_type = "trial_minus_24h"
            if msg_type:
                await notifier.send_trial_notification(user, msg_type)


async def run_subscription_notifications(bot: Bot) -> None:
    """Subscription expiry: -3d, -24h, -3h, expired."""
    session_factory = get_async_session_maker()
    async with session_factory() as session:
        result = await session.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(Subscription.is_active == True)
        )
        rows = result.all()
        notifier = NotificationService(bot)
        now = datetime.utcnow()
        for sub, user in rows:
            delta = (sub.expires_at - now).total_seconds() / 3600
            msg_type = None
            if delta <= 0:
                msg_type = "sub_expired"
            elif 0 < delta <= 3:
                msg_type = "sub_minus_3h"
            elif 3 < delta <= 24:
                msg_type = "sub_minus_24h"
            elif 24 < delta <= 72:
                msg_type = "sub_minus_3d"
            if msg_type:
                await notifier.send_subscription_notification(user, msg_type)
