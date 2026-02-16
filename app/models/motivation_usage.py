"""Motivation phrase usage — per user per habit."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MotivationUsage(Base):
    __tablename__ = "motivation_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    habit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    phrase_index: Mapped[int] = mapped_column(Integer, nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
