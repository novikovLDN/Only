"""
Smart Insights Engine — персональные подсказки на основе агрегатов.
"""

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.habit_repo import HabitRepository


@dataclass
class InsightInput:
    """Input data for insight selection."""

    completed: int
    skipped: int
    streak_days: int
    completion_rate_pct: float
    completed_7d: int
    skipped_7d: int
    last_activity_date: date | None
    evening_skips_pct: float | None  # % of skips in evening hours
    morning_complete_pct: float | None  # % of completes in morning


INSIGHTS_POOL = [
    "Ты в отличном темпе — главное не сбавлять! 💪",
    "Маленькие шаги каждый день ведут к большим результатам. ✨",
    "Дисциплина — мост между целями и достижениями. 🌉",
    "Каждый день — новая возможность стать лучше. 🚀",
    "Одна пауза — не провал. Продолжай сегодня. 🔄",
    "Консистентность важнее интенсивности. Ты молодец! 👏",
    "Будущее создаётся сегодня. Ты уже в пути. ⭐",
]

INSIGHT_COMPLETION_HIGH = (
    "Ты в отличном темпе — главное не сбавлять! 💪"
)
INSIGHT_EVENING_SKIPS = (
    "Вечером привычки даются сложнее — попробуй утро. 🌅"
)
INSIGHT_STREAK_BROKEN = (
    "Одна пауза — не провал. Продолжай сегодня. 🔄"
)
INSIGHT_NO_ACTIVITY = (
    "Мы скучаем 😔 Маленький шаг сегодня — уже победа."
)
INSIGHT_MORNING_BEST = (
    "Ты чаще всего выполняешь привычки утром — попробуй добавить ещё одну в это время. 🌅"
)


class InsightsService:
    """Generate personalized insights."""

    def __init__(self, session: AsyncSession) -> None:
        self._habit_repo = HabitRepository(session)

    async def get_insight_for_profile(
        self, user_id: int, last_insight_id: int | None, last_insight_at: datetime | None
    ) -> tuple[str, int]:
        """
        Get insight for profile screen. Returns (insight_text, insight_index).
        Avoids repeating same insight for 24h.
        """
        completed = await self._habit_repo.count_user_completed_logs(user_id)
        skipped = await self._habit_repo.count_user_skipped_logs(user_id)
        streak = await self._habit_repo.get_current_streak(user_id)
        last_activity = await self._habit_repo.get_last_activity_date(user_id)

        total = completed + skipped
        completion_rate = (completed / total * 100) if total > 0 else 0

        today = date.today()
        week_ago = today - timedelta(days=7)
        logs_7d = await self._habit_repo.get_user_logs_per_day(user_id, week_ago, today)
        completed_7d = sum(r[1] for r in logs_7d)
        skipped_7d = sum(r[2] for r in logs_7d)

        # Build candidate insights by rules
        candidates: list[tuple[str, int]] = []
        now = datetime.now(timezone.utc)
        for i, text in enumerate(INSIGHTS_POOL):
            if last_insight_id == i and last_insight_at:
                at = last_insight_at
                if at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)
                if (now - at).total_seconds() < 86400:
                    continue  # skip if shown < 24h ago
            candidates.append((text, i))

        # Rule-based priority
        if completion_rate >= 80 and total >= 5:
            candidates.insert(0, (INSIGHT_COMPLETION_HIGH, len(INSIGHTS_POOL)))
        if streak == 0 and last_activity and (today - last_activity).days >= 1:
            candidates.insert(0, (INSIGHT_STREAK_BROKEN, len(INSIGHTS_POOL) + 1))
        if last_activity and (today - last_activity).days >= 2:
            candidates.insert(0, (INSIGHT_NO_ACTIVITY, len(INSIGHTS_POOL) + 2))
        if completed_7d >= 5 and completed_7d > skipped_7d * 2:
            candidates.insert(0, (INSIGHT_MORNING_BEST, len(INSIGHTS_POOL) + 3))

        if not candidates:
            return INSIGHTS_POOL[0], 0
        text, idx = random.choice(candidates[: min(5, len(candidates))])
        return text, idx
