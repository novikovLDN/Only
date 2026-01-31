"""
Habit schedule — расписание напоминаний.

reminder_time: HH:MM в часовом поясе пользователя.
days_of_week: "0,1,2,3,4,5,6" (Mon-Sun) для weekly/custom.
"""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.constants import HabitScheduleType
from app.models.base import Base, TimestampMixin


class HabitSchedule(Base, TimestampMixin):
    """Schedule for habit reminder."""

    __tablename__ = "habit_schedules"
    __table_args__ = (
        CheckConstraint(
            "schedule_type IN ('daily', 'weekly', 'custom')",
            name="ck_habit_schedules_type",
        ),
        Index("ix_habit_schedules_habit_enabled", "habit_id", "is_enabled"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schedule_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=HabitScheduleType.DAILY,
    )
    reminder_time: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        comment="HH:MM в timezone пользователя",
    )
    days_of_week: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="0,1,2,3,4,5,6 для weekly",
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    habit = relationship("Habit", back_populates="schedules")

    def __repr__(self) -> str:
        return f"<HabitSchedule(id={self.id}, habit_id={self.habit_id}, time={self.reminder_time})>"
