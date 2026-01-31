"""
Job runners — idempotent wrappers с проверкой статуса и логированием.
"""

import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy import select

from app.config.constants import UserTier
from app.models.base import get_async_session_maker
from app.models.habit import Habit
from app.models.habit_schedule import HabitSchedule
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.subscription_repo import SubscriptionRepository
from app.scheduler.job_logger import job_execution_log, log_job_skip
from app.services.notification_service import NotificationService
from app.utils.timezone import to_user_tz, utc_now

# For DB datetime comparison (may be naive)
def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

logger = logging.getLogger(__name__)


def _should_notify_user(user: User) -> bool:
    """Проверка: пользователь активен, не заблокирован."""
    return not user.is_blocked


def _user_has_active_access(user: User, sub: Subscription | None) -> bool:  # noqa: ARG001
    """Проверка: trial активен или есть активная подписка."""
    if user.tier == UserTier.PREMIUM and sub:
        return sub.is_active and sub.expires_at > datetime.now(timezone.utc)
    if user.tier == UserTier.TRIAL and user.trial_ends_at:
        return user.trial_ends_at > datetime.now(timezone.utc)
    if user.tier == UserTier.FREE:
        return True
    return False


async def run_habit_reminders_job(bot: Bot) -> None:
    """
    Idempotent: проверяем время в user timezone, статус пользователя.
    """
    async with job_execution_log("habit_reminders"):
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            now_utc = utc_now()
            result = await session.execute(
                select(HabitSchedule, Habit, User)
                .join(Habit, Habit.id == HabitSchedule.habit_id)
                .join(User, User.id == Habit.user_id)
                .where(HabitSchedule.is_enabled == True)
                .where(Habit.is_active == True)
            )
            rows = result.all()
            notifier = NotificationService(bot)
            sent = 0
            for sched, habit, user in rows:
                try:
                    if not _should_notify_user(user):
                        log_job_skip("habit_reminders", "user_blocked", user_id=user.id)
                        continue
                    user_now = to_user_tz(now_utc, user.timezone)
                    h, m = map(int, sched.reminder_time.split(":")[:2])
                    if user_now.hour != h or user_now.minute >= 5:
                        continue
                    from app.keyboards.main_menu import habit_reminder_keyboard

                    ok = await notifier.send_habit_reminder(
                        user, habit, habit_reminder_keyboard(habit.id)
                    )
                    if ok:
                        sent += 1
                except Exception as e:
                    log_job_skip("habit_reminders", "error", habit_id=habit.id, error=str(e))
            if sent:
                logger.info("habit_reminders: sent %d", sent)


async def run_trial_notifications_job(bot: Bot) -> None:
    """
    Idempotent: проверяем актуальный tier, trial_ends_at перед отправкой.
    """
    async with job_execution_log("trial_notifications"):
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            now = utc_now()
            result = await session.execute(
                select(User)
                .where(User.tier == UserTier.TRIAL)
                .where(User.trial_ends_at.isnot(None))
            )
            users = result.scalars().all()
            notifier = NotificationService(bot)
            sent = 0
            for user in users:
                try:
                    if not _should_notify_user(user) or not user.trial_ends_at:
                        continue
                    ends_at = _as_utc(user.trial_ends_at)
                    if ends_at is None:
                        continue
                    delta_h = (ends_at - now).total_seconds() / 3600
                    msg_type = None
                    if delta_h <= 0:
                        msg_type = "trial_expired"
                    elif 0 < delta_h <= 3:
                        msg_type = "trial_minus_3h"
                    elif 3 < delta_h <= 24:
                        msg_type = "trial_minus_24h"
                    if msg_type:
                        ok = await notifier.send_trial_notification(user, msg_type)
                        if ok:
                            sent += 1
                except Exception as e:
                    log_job_skip("trial_notifications", "error", user_id=user.id, error=str(e))
            if sent:
                logger.info("trial_notifications: sent %d", sent)


async def run_subscription_notifications_job(bot: Bot) -> None:
    """
    Idempotent: проверяем subscription.is_active, expires_at.
    """
    async with job_execution_log("subscription_notifications"):
        session_factory = get_async_session_maker()
        async with session_factory() as session:
            result = await session.execute(
                select(Subscription, User)
                .join(User, User.id == Subscription.user_id)
                .where(Subscription.is_active == True)
            )
            rows = result.all()
            notifier = NotificationService(bot)
            now = utc_now()
            sent = 0
            for sub, user in rows:
                try:
                    if not _should_notify_user(user):
                        continue
                    expires_at = _as_utc(sub.expires_at)
                    if expires_at is None:
                        continue
                    delta_h = (expires_at - now).total_seconds() / 3600
                    msg_type = None
                    if delta_h <= 0:
                        msg_type = "sub_expired"
                    elif 0 < delta_h <= 3:
                        msg_type = "sub_minus_3h"
                    elif 3 < delta_h <= 24:
                        msg_type = "sub_minus_24h"
                    elif 24 < delta_h <= 72:
                        msg_type = "sub_minus_3d"
                    if msg_type:
                        ok = await notifier.send_subscription_notification(user, msg_type)
                        if ok:
                            sent += 1
                except Exception as e:
                    log_job_skip(
                        "subscription_notifications",
                        "error",
                        sub_id=sub.id,
                        error=str(e),
                    )
            if sent:
                logger.info("subscription_notifications: sent %d", sent)


# Track last known failures for recovery notifications
_health_failures: set[str] = set()


async def run_health_check_job(bot: Bot) -> None:
    """
    System health check — db, scheduler, bot. Alerts on failure, recovery when fixed.
    """
    async with job_execution_log("health_check"):
        from app.config.constants import AlertSeverity
        from app.monitoring.admin_alert_service import AdminAlertService
        from app.monitoring.monitoring_service import MonitoringService

        svc = MonitoringService(bot)
        health = await svc.run_health_checks()
        alert_svc = AdminAlertService(bot)
        current_failures = {n for n, c in health.components.items() if not c.ok}
        for name, comp in health.components.items():
            if not comp.ok:
                fp = f"health:{name}"
                severity = AlertSeverity.CRITICAL if name == "database" else AlertSeverity.WARNING
                await alert_svc.send_alert(
                    severity=severity,
                    source="health_check",
                    message=f"{name}: {comp.message or 'unavailable'}",
                    fingerprint=fp,
                    details={"component": name},
                )
                _health_failures.add(name)
                await svc.log_to_db(
                    severity=severity.value,
                    source="health_check",
                    message=f"{name} failed: {comp.message}",
                    fingerprint=fp,
                )
            elif name in _health_failures:
                await alert_svc.send_recovery(name, f"{name} is back online")
                _health_failures.discard(name)
                await svc.log_to_db("info", "health_check", f"{name} recovered")
        if health.ok:
            await svc.log_to_db("info", "health_check", "All checks passed")


async def run_subscription_renew_job(bot: Bot) -> None:
    """
    Autorenew: списать с баланса за 24h до истечения.
    Retry: повторная попытка через 72h после неуспеха.
    """
    async with job_execution_log("subscription_renew"):
        from app.services.subscription_renew_service import SubscriptionRenewService
        from app.services.notification_service import NotificationService

        session_factory = get_async_session_maker()
        async with session_factory() as session:
            sub_repo = SubscriptionRepository(session)
            renew_svc = SubscriptionRenewService(session)
            notifier = NotificationService(bot)
            renewed = 0
            for sub, user in await sub_repo.get_expiring_for_renewal(within_hours=24):
                try:
                    if not _should_notify_user(user):
                        continue
                    ok, err = await renew_svc.try_renew_from_balance(sub, user)
                    if ok:
                        await notifier.send_renewal_success(user)
                        renewed += 1
                    else:
                        await renew_svc.mark_renewal_attempted(sub)
                        if "balance" in (err or "").lower():
                            await notifier.send_renewal_failed_insufficient(user)
                except Exception as e:
                    log_job_skip("subscription_renew", "error", sub_id=sub.id, error=str(e))
            for sub, user in await sub_repo.get_expired_for_retry(retry_cooldown_hours=72):
                try:
                    if not _should_notify_user(user):
                        continue
                    ok, err = await renew_svc.try_renew_from_balance(sub, user)
                    if ok:
                        await notifier.send_renewal_success(user)
                        renewed += 1
                    else:
                        await renew_svc.mark_renewal_attempted(sub)
                except Exception as e:
                    log_job_skip("subscription_renew_retry", "error", sub_id=sub.id, error=str(e))
            await session.commit()
            if renewed:
                logger.info("subscription_renew: renewed %d", renewed)


async def run_retention_job(bot: Bot) -> None:
    """
    Retention: inactivity reminders, streak milestones.
    """
    async with job_execution_log("retention"):
        from app.services.retention_service import RetentionService
        from app.services.notification_service import NotificationService

        session_factory = get_async_session_maker()
        async with session_factory() as session:
            retention_svc = RetentionService(session)
            notifier = NotificationService(bot)
            sent = 0
            for user in await retention_svc.get_users_for_inactivity_reminder():
                try:
                    if not _should_notify_user(user):
                        continue
                    if await notifier.send_inactivity_reminder(user):
                        await retention_svc.mark_inactivity_reminder_sent(user)
                        sent += 1
                except Exception as e:
                    log_job_skip("retention_inactivity", "error", user_id=user.id, error=str(e))
            for user, milestone in await retention_svc.get_users_for_streak_milestone():
                try:
                    if not _should_notify_user(user):
                        continue
                    if await notifier.send_streak_milestone(user, milestone):
                        await retention_svc.mark_streak_milestone_sent(user, milestone)
                        sent += 1
                except Exception as e:
                    log_job_skip("retention_streak", "error", user_id=user.id, error=str(e))
            await session.commit()
            if sent:
                logger.info("retention: sent %d", sent)


async def run_analytics_refresh_job() -> None:
    """Refresh cached analytics metrics (DAU, WAU, MAU, conversion, churn, completion)."""
    async with job_execution_log("analytics_refresh"):
        from app.models.base import get_async_session_maker
        from app.services.analytics_service import AnalyticsService

        session_factory = get_async_session_maker()
        async with session_factory() as session:
            svc = AnalyticsService(session)
            await svc.refresh_all_metrics()
