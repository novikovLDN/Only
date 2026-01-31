"""
Achievement model — награды за прогресс.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Achievement(Base, TimestampMixin):
    """Achievement definition."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False, default="🏆")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    condition_type: Mapped[str] = mapped_column(String(32), nullable=False)
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user_achievements = relationship("UserAchievement", back_populates="achievement")

    def __repr__(self) -> str:
        return f"<Achievement(code={self.code})>"
