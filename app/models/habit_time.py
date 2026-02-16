"""HabitTime — weekday + time (TIME type)."""

from datetime import time

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HabitTime(Base):
    __tablename__ = "habit_times"
    __table_args__ = (UniqueConstraint("habit_id", "weekday", "time", name="uq_habit_time_weekday_time"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    time: Mapped[time] = mapped_column(Time, nullable=False)

    habit: Mapped["Habit"] = relationship("Habit", back_populates="habit_times")
