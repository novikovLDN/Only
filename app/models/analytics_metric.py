"""
Analytics metric — кеш предрассчитанных метрик.

Scheduler обновляет значения. Admin dashboard читает из кеша.
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AnalyticsMetric(Base, TimestampMixin):
    """Cached analytics metric (key-value)."""

    __tablename__ = "analytics_metrics"
    __table_args__ = (
        Index("ix_analytics_metrics_key", "metric_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    metric_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Ключ метрики: dau, wau, mau, conversion, churn, completion_rate",
    )
    value_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="JSON: число, объект или массив",
    )
    computed_at: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ISO datetime расчёта",
    )

    def __repr__(self) -> str:
        return f"<AnalyticsMetric(key={self.metric_key})>"
