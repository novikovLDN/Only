"""
Habit log — completion/decline tracking.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class HabitLog(Base, TimestampMixin):
    """Log entry for habit completion or skip."""

    __tablename__ = "habit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False)  # True = done, False = declined
    decline_note_id: Mapped[int | None] = mapped_column(ForeignKey("decline_notes.id", ondelete="SET NULL"), nullable=True)

    habit = relationship("Habit", back_populates="logs")

    def __repr__(self) -> str:
        return f"<HabitLog(id={self.id}, habit_id={self.habit_id}, date={self.log_date}, completed={self.completed})>"
