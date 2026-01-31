"""Analytics repository — cache and raw queries."""

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    """Analytics cache and aggregation queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_metric(self, key: str, value_json: str, computed_at: str) -> None:
        """Insert or update cached metric."""
        await self._session.execute(
            text(
                """
                INSERT INTO analytics_metrics (metric_key, value_json, computed_at, created_at, updated_at)
                VALUES (:key, :value_json, :computed_at, NOW(), NOW())
                ON CONFLICT (metric_key) DO UPDATE SET
                    value_json = EXCLUDED.value_json,
                    computed_at = EXCLUDED.computed_at,
                    updated_at = NOW()
                """
            ),
            {"key": key, "value_json": value_json, "computed_at": computed_at},
        )

    async def get_metric(self, key: str) -> tuple[str | None, str | None]:
        """Get cached metric (value_json, computed_at). Returns (None, None) if not found."""
        result = await self._session.execute(
            text(
                "SELECT value_json, computed_at FROM analytics_metrics WHERE metric_key = :key"
            ),
            {"key": key},
        )
        row = result.fetchone()
        if row:
            return (row[0], row[1])
        return (None, None)

    async def get_all_metrics(self) -> dict[str, tuple[str, str]]:
        """Get all cached metrics: {key: (value_json, computed_at)}."""
        result = await self._session.execute(
            text("SELECT metric_key, value_json, computed_at FROM analytics_metrics")
        )
        return {row[0]: (row[1], row[2]) for row in result.fetchall()}

    # --- Raw aggregation queries (for scheduler job) ---

    async def compute_dau(self, for_date: date | None = None) -> int:
        """DAU: distinct users who logged a habit (completed or declined) on date."""
        d = for_date or datetime.now(timezone.utc).date()
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT h.user_id)
                FROM habit_logs hl
                JOIN habits h ON h.id = hl.habit_id
                WHERE hl.log_date = :d
                """
            ),
            {"d": d},
        )
        return result.scalar() or 0

    async def compute_wau(self, for_date: date | None = None) -> int:
        """WAU: distinct users with habit_log in last 7 days ending on for_date."""
        end = for_date or datetime.now(timezone.utc).date()
        start = end - timedelta(days=6)
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT h.user_id)
                FROM habit_logs hl
                JOIN habits h ON h.id = hl.habit_id
                WHERE hl.log_date >= :start AND hl.log_date <= :end
                """
            ),
            {"start": start, "end": end},
        )
        return result.scalar() or 0

    async def compute_mau(self, for_date: date | None = None) -> int:
        """MAU: distinct users with habit_log in last 30 days ending on for_date."""
        end = for_date or datetime.now(timezone.utc).date()
        start = end - timedelta(days=29)
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT h.user_id)
                FROM habit_logs hl
                JOIN habits h ON h.id = hl.habit_id
                WHERE hl.log_date >= :start AND hl.log_date <= :end
                """
            ),
            {"start": start, "end": end},
        )
        return result.scalar() or 0

    async def compute_trial_conversion(self) -> dict[str, Any]:
        """
        Trial → paid conversion.
        conversion = users with paid sub / users who ended trial (free + premium).
        """
        result = await self._session.execute(
            text(
                """
                WITH trial_ended AS (
                    SELECT COUNT(*) AS cnt FROM users WHERE tier IN ('free', 'premium')
                ),
                paid_users AS (
                    SELECT COUNT(DISTINCT user_id) AS cnt
                    FROM subscriptions
                    WHERE payment_id IS NOT NULL
                )
                SELECT te.cnt AS trial_ended, pu.cnt AS paid
                FROM trial_ended te, paid_users pu
                """
            )
        )
        row = result.fetchone()
        trial_ended = row[0] or 0
        paid = row[1] or 0
        rate = (paid / trial_ended * 100) if trial_ended > 0 else 0.0
        return {"trial_ended": trial_ended, "paid": paid, "conversion_pct": round(rate, 2)}

    async def compute_churn(self) -> dict[str, Any]:
        """
        Subscription churn: subs expired in last 30d.
        churn_rate = expired_in_period / (active_now + expired_in_period).
        """
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)
        result = await self._session.execute(
            text(
                """
                WITH expired_in_period AS (
                    SELECT COUNT(*) AS cnt
                    FROM subscriptions
                    WHERE expires_at >= :month_ago
                      AND expires_at < :now
                ),
                active_now AS (
                    SELECT COUNT(*) AS cnt
                    FROM subscriptions
                    WHERE is_active = 1 AND expires_at > :now
                )
                SELECT ep.cnt AS expired, an.cnt AS active
                FROM expired_in_period ep, active_now an
                """
            ),
            {"month_ago": month_ago, "now": now},
        )
        row = result.fetchone()
        expired = row[0] or 0
        active = row[1] or 0
        rate = (expired / (active + expired) * 100) if (active + expired) > 0 else 0.0
        return {"expired_30d": expired, "active_now": active, "churn_pct": round(rate, 2)}

    async def compute_habit_completion_rate(self, days: int = 30) -> dict[str, Any]:
        """
        Habit completion rate: completed / total logs in period.
        completed=True → done, False → declined.
        """
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
        result = await self._session.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE completed = true) AS completed,
                    COUNT(*) AS total
                FROM habit_logs
                WHERE log_date >= :cutoff
                """
            ),
            {"cutoff": cutoff},
        )
        row = result.fetchone()
        completed = row[0] or 0
        total = row[1] or 0
        rate = (completed / total * 100) if total > 0 else 0.0
        return {"completed": completed, "total": total, "completion_pct": round(rate, 2)}
