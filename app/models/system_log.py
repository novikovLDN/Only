"""
System log — errors, events for monitoring.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.constants import AlertSeverity
from app.models.base import Base, TimestampMixin


class SystemLog(Base, TimestampMixin):
    """System event/error log for monitoring."""

    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # For deduplication
    alerted_at: Mapped[str | None] = mapped_column(String(50), nullable=True)  # ISO datetime when alert sent

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, severity={self.severity}, source={self.source})>"
