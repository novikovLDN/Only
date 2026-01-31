"""
Admin alert — история отправленных алертов.

Дедупликация: один fingerprint не дублируется в интервале.
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AdminAlert(Base, TimestampMixin):
    """Admin alert record for deduplication and audit."""

    __tablename__ = "admin_alerts"
    __table_args__ = (
        Index("ix_admin_alerts_fingerprint_created", "fingerprint", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Hash для дедупликации",
    )

    def __repr__(self) -> str:
        return f"<AdminAlert(id={self.id}, severity={self.severity})>"
