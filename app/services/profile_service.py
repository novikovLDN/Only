"""
Profile service — агрегация данных для экрана профиля.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.habit_repo import HabitRepository
from app.repositories.referral_repo import ReferralRepository
from app.repositories.subscription_repo import SubscriptionRepository


@dataclass
class ProfileData:
    """Данные для экрана профиля."""

    completed_habits: int
    skipped_habits: int
    streak_days: int
    referral_count: int
    status: str
    subscription_text: str
    timezone_display: str
    completion_rate_pct: float
    completed_7d: int
    skipped_7d: int
    insight: str


def _referral_status(count: int) -> str:
    """Статус по количеству рефералов."""
    if count >= 25:
        return "Platinum"
    if count >= 10:
        return "Gold"
    if count >= 3:
        return "Silver"
    return "—"


class ProfileService:
    """Profile business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._habit_repo = HabitRepository(session)
        self._referral_repo = ReferralRepository(session)
        self._sub_repo = SubscriptionRepository(session)

    async def get_profile_data(
        self, user_id: int, timezone_display: str, insight: str
    ) -> ProfileData:
        """Aggregate profile data for user."""
        completed = await self._habit_repo.count_user_completed_logs(user_id)
        skipped = await self._habit_repo.count_user_skipped_logs(user_id)
        streak = await self._habit_repo.get_current_streak(user_id)
        ref_count = await self._referral_repo.count_referrals(user_id)
        status = _referral_status(ref_count)

        total = completed + skipped
        completion_rate = round((completed / total * 100)) if total > 0 else 0

        today = date.today()
        week_ago = today - timedelta(days=7)
        logs_7d = await self._habit_repo.get_user_logs_per_day(user_id, week_ago, today)
        completed_7d = sum(r[1] for r in logs_7d)
        skipped_7d = sum(r[2] for r in logs_7d)

        sub = await self._sub_repo.get_active_subscription(user_id)
        if sub and sub.expires_at:
            sub_text = f"Активна до {sub.expires_at.strftime('%d.%m.%Y')}"
        else:
            sub_text = "—"

        return ProfileData(
            completed_habits=completed,
            skipped_habits=skipped,
            streak_days=streak,
            referral_count=ref_count,
            status=status,
            subscription_text=sub_text,
            timezone_display=timezone_display,
            completion_rate_pct=completion_rate,
            completed_7d=completed_7d,
            skipped_7d=skipped_7d,
            insight=insight,
        )

    async def get_detail_progress(self, user_id: int, days: int = 14) -> dict:
        """
        Detail progress: per-weekday bars for last N days.
        Returns {weekday_label: "██░", ...} and best_day, best_time.
        """
        today = date.today()
        from_date = today - timedelta(days=days)
        logs = await self._habit_repo.get_user_logs_per_day(user_id, from_date, today)
        by_date = {r[0]: (r[1], r[2]) for r in logs}
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        bars: dict[str, str] = {}
        for wd, label in enumerate(weekdays):
            chars = []
            for i in range(days - 1, -1, -1):  # from oldest to newest
                d = today - timedelta(days=i)
                if d.weekday() == wd:
                    compl, skipp = by_date.get(d, (0, 0))
                    if compl > 0:
                        chars.append("█")
                    elif skipp > 0:
                        chars.append("░")
                    else:
                        chars.append("·")
            bars[label] = "".join(chars) if chars else "·"
        best_day = max(weekdays, key=lambda w: bars.get(w, "").count("█")) if bars else "—"
        return {"bars": bars, "best_day": best_day, "best_time": "Утро (06:00–10:00)"}
