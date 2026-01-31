"""
Habit decline note — причина пропуска привычки.

Отдельная таблица для нормализации; одна запись на один пропуск.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class HabitDeclineNote(Base, TimestampMixin):
    """User-provided reason for declining/skipping a habit."""

    __tablename__ = "habit_decline_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    preset: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="sick, busy, tired и т.д.",
    )

    def __repr__(self) -> str:
        return f"<HabitDeclineNote(id={self.id}, preset={self.preset})>"
