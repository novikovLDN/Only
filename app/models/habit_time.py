"""HabitTime — weekday + time slots per habit."""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HabitTime(Base):
    __tablename__ = "habit_times"
    __table_args__ = (UniqueConstraint("habit_id", "weekday", "time", name="uq_habit_time_weekday_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=mon, 6=sun
    time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM

    habit: Mapped["Habit"] = relationship("Habit", back_populates="habit_times")
