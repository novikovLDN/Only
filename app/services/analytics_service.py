"""
AnalyticsService — расчёт и кеширование метрик.

Тяжёлые запросы выполняются в scheduler job. Dashboard читает из кеша.
"""

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.repositories.analytics_repo import AnalyticsRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Keys for analytics_metrics cache
KEY_DAU = "dau"
KEY_WAU = "wau"
KEY_MAU = "mau"
KEY_TRIAL_CONVERSION = "trial_conversion"
KEY_CHURN = "churn"
KEY_COMPLETION_RATE = "completion_rate"
KEY_AGGREGATE = "analytics_aggregate"


class AnalyticsService:
    """Compute and cache product analytics."""

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def refresh_all_metrics(self) -> None:
        """Run all aggregations and write to cache. Called by scheduler."""
        now = datetime.now(timezone.utc)
        today = now.date()
        computed_at = now.isoformat()
        try:
            dau = await self._repo.compute_dau(today)
            wau = await self._repo.compute_wau(today)
            mau = await self._repo.compute_mau(today)
            conversion = await self._repo.compute_trial_conversion()
            churn = await self._repo.compute_churn()
            completion = await self._repo.compute_habit_completion_rate(30)

            await self._repo.upsert_metric(KEY_DAU, json.dumps(dau), computed_at)
            await self._repo.upsert_metric(KEY_WAU, json.dumps(wau), computed_at)
            await self._repo.upsert_metric(KEY_MAU, json.dumps(mau), computed_at)
            await self._repo.upsert_metric(
                KEY_TRIAL_CONVERSION, json.dumps(conversion), computed_at
            )
            await self._repo.upsert_metric(KEY_CHURN, json.dumps(churn), computed_at)
            await self._repo.upsert_metric(
                KEY_COMPLETION_RATE, json.dumps(completion), computed_at
            )

            aggregate = {
                "dau": dau,
                "wau": wau,
                "mau": mau,
                "trial_conversion": conversion,
                "churn": churn,
                "completion_rate": completion,
            }
            await self._repo.upsert_metric(
                KEY_AGGREGATE, json.dumps(aggregate), computed_at
            )
            await self._session.commit()
            logger.info("Analytics metrics refreshed at %s", computed_at)
        except Exception as e:
            logger.exception("Analytics refresh failed: %s", e)
            await self._session.rollback()
            raise

    async def get_cached_aggregate(self) -> dict[str, Any] | None:
        """Get all metrics from cache. Returns None if not yet computed."""
        value, _ = await self._repo.get_metric(KEY_AGGREGATE)
        if value:
            return json.loads(value)
        return None

    async def get_cached_metric(self, key: str) -> tuple[Any | None, str | None]:
        """Get single metric (parsed value, computed_at)."""
        value, computed_at = await self._repo.get_metric(key)
        if value:
            try:
                return json.loads(value), computed_at
            except json.JSONDecodeError:
                return value, computed_at
        return None, None
