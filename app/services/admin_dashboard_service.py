"""
AdminDashboardService — данные для админ-панели.

Данные через сервис, не напрямую из БД в handler.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.config.constants import UserTier
from app.repositories.admin_alert_repo import AdminAlertRepository
from app.repositories.balance_repo import BalanceRepository
from app.repositories.habit_repo import HabitRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.system_log_repo import SystemLogRepository
from app.repositories.user_repo import UserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AdminDashboardService:
    """Aggregates admin dashboard data from repositories."""

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session

    async def get_system_status(self, bot_alive: bool = True) -> str:
        """System status: db, scheduler, bot."""
        from sqlalchemy import text

        from app.scheduler.init import get_scheduler

        db_ok = True
        try:
            await self._session.execute(text("SELECT 1"))
        except Exception:
            db_ok = False

        sched_ok = False
        try:
            sched_ok = get_scheduler().running
        except Exception:
            pass

        parts = ["<b>System Status</b>\n"]
        parts.append(f"{'🟢' if db_ok else '🔴'} DB: {'OK' if db_ok else 'FAIL'}")
        parts.append(f"{'🟢' if sched_ok else '🔴'} Scheduler: {'OK' if sched_ok else 'FAIL'}")
        parts.append(f"{'🟢' if bot_alive else '🔴'} Bot: {'OK' if bot_alive else 'FAIL'}")
        return "\n".join(parts)

    async def get_users_stats(self) -> str:
        """Users overview."""
        user_repo = UserRepository(self._session)
        habit_repo = HabitRepository(self._session)

        total = await user_repo.count_all()
        trial = await user_repo.count_by_tier(UserTier.TRIAL)
        free = await user_repo.count_by_tier(UserTier.FREE)
        premium = await user_repo.count_by_tier(UserTier.PREMIUM)
        new_today = await user_repo.count_created_since_days(1)
        new_week = await user_repo.count_created_since_days(7)

        from sqlalchemy import select, func

        from app.models.habit import Habit

        habits_result = await self._session.execute(select(func.count(Habit.id)))
        habits_count = habits_result.scalar() or 0

        return (
            f"<b>Users</b>\n\n"
            f"👥 Total: {total}\n"
            f"· Trial: {trial} | Free: {free} | Premium: {premium}\n"
            f"· New today: {new_today} | 7d: {new_week}\n"
            f"📋 Habits: {habits_count}"
        )

    async def get_subscriptions_stats(self) -> str:
        """Subscriptions overview."""
        sub_repo = SubscriptionRepository(self._session)
        active = await sub_repo.count_active()
        revenue = await sub_repo.sum_revenue()
        expiring = await sub_repo.get_expiring_soon(72)
        return (
            f"<b>Subscriptions</b>\n\n"
            f"✅ Active: {active}\n"
            f"💰 Revenue (subs): {revenue:.2f}\n"
            f"⏳ Expiring 72h: {len(expiring)}"
        )

    async def get_finance_stats(self) -> str:
        """Finance overview."""
        pay_repo = PaymentRepository(self._session)
        bal_repo = BalanceRepository(self._session)

        pay_count = await pay_repo.count_completed()
        pay_sum = await pay_repo.sum_completed()
        bal_total = await bal_repo.sum_total()

        return (
            f"<b>Finance</b>\n\n"
            f"💳 Payments (succeeded): {pay_count}\n"
            f"💰 Sum: {pay_sum}\n"
            f"🏦 Balances total: {bal_total}"
        )

    async def get_analytics(self) -> str:
        """Analytics summary — from cache (DAU, WAU, MAU, conversion, churn, completion)."""
        from app.services.analytics_service import AnalyticsService

        svc = AnalyticsService(self._session)
        cached = await svc.get_cached_aggregate()
        if cached:
            dau = cached.get("dau", 0)
            wau = cached.get("wau", 0)
            mau = cached.get("mau", 0)
            conv = cached.get("trial_conversion", {})
            churn = cached.get("churn", {})
            comp = cached.get("completion_rate", {})
            conv_pct = conv.get("conversion_pct", 0)
            churn_pct = churn.get("churn_pct", 0)
            comp_pct = comp.get("completion_pct", 0)
            return (
                f"<b>Analytics</b>\n\n"
                f"📊 Activity:\n"
                f"· DAU: {dau} | WAU: {wau} | MAU: {mau}\n\n"
                f"📈 Conversion (trial→paid): {conv_pct}%\n"
                f"· Paid: {conv.get('paid', 0)} / ended: {conv.get('trial_ended', 0)}\n\n"
                f"📉 Churn (30d): {churn_pct}%\n"
                f"· Expired: {churn.get('expired_30d', 0)} | Active: {churn.get('active_now', 0)}\n\n"
                f"✅ Completion rate (30d): {comp_pct}%\n"
                f"· Done: {comp.get('completed', 0)} / {comp.get('total', 0)}"
            )
        user_repo = UserRepository(self._session)
        new_today = await user_repo.count_created_since_days(1)
        new_week = await user_repo.count_created_since_days(7)
        new_month = await user_repo.count_created_since_days(30)
        return (
            f"<b>Analytics</b>\n\n"
            f"⏳ Метрики ещё не рассчитаны (scheduler).\n\n"
            f"📈 New users:\n"
            f"· 24h: {new_today} | 7d: {new_week} | 30d: {new_month}"
        )

    async def get_errors_alerts(self, limit: int = 5) -> str:
        """Recent errors and alerts."""
        log_repo = SystemLogRepository(self._session)
        alert_repo = AdminAlertRepository(self._session)

        errors = await log_repo.get_recent(
            severities=["critical", "warning"], limit=limit
        )
        alerts = await alert_repo.get_recent(limit=limit)

        lines = ["<b>Errors & Alerts</b>\n"]
        if errors:
            lines.append("⚠️ Logs:")
            for e in errors[:3]:
                ts = e.created_at.strftime("%m/%d %H:%M") if e.created_at else "—"
                lines.append(f"· [{ts}] {e.message[:50]}...")
        else:
            lines.append("✅ No recent errors")

        if alerts:
            lines.append("\n🚨 Alerts:")
            for a in alerts[:3]:
                ts = a.created_at.strftime("%m/%d %H:%M") if a.created_at else "—"
                lines.append(f"· [{ts}] {a.severity}: {a.message[:40]}...")
        else:
            lines.append("\n✅ No recent alerts")

        return "\n".join(lines)
