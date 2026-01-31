"""
System log — события и ошибки для мониторинга.

fingerprint — для дедупликации алертов.
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SystemLog(Base, TimestampMixin):
    """System event/error log for monitoring."""

    __tablename__ = "system_logs"
    __table_args__ = (
        Index("ix_system_logs_fingerprint_created", "fingerprint", "created_at"),
        Index("ix_system_logs_severity_created", "severity", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Hash для дедупликации алертов",
    )
    alerted_at: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="ISO datetime когда отправлен alert",
    )

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, severity={self.severity})>"
