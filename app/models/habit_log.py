"""HabitLog — done/skipped per habit per date."""

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # done | skipped
    skip_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    habit: Mapped["Habit"] = relationship("Habit", back_populates="habit_logs")
    user: Mapped["User"] = relationship("User", back_populates="habit_logs")
