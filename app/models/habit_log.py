"""
Habit log — фиксация выполнения или пропуска.

Unique (habit_id, log_date) — один лог на привычку в день.
Индекс для аналитики completion rate.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class HabitLog(Base, TimestampMixin):
    """Log entry for habit completion or skip."""

    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint("habit_id", "log_date", name="uq_habit_logs_habit_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False)  # True = done, False = declined
    decline_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("habit_decline_notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    habit = relationship("Habit", back_populates="logs")

    def __repr__(self) -> str:
        return f"<HabitLog(id={self.id}, habit_id={self.habit_id}, date={self.log_date}, completed={self.completed})>"
