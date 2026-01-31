"""
Habit model.

Связь habit_logs — для аналитики completion rate.
"""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Habit(Base, TimestampMixin):
    """User habit."""

    __tablename__ = "habits"
    __table_args__ = (
        Index("ix_habits_user_created", "user_id", "created_at"),  # Список привычек пользователя
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)

    user = relationship("User", back_populates="habits")
    schedules = relationship("HabitSchedule", back_populates="habit", cascade="all, delete-orphan")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Habit(id={self.id}, name={self.name})>"
