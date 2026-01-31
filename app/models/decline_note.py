"""
Decline note — reason for skipping habit.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DeclineNote(Base, TimestampMixin):
    """User-provided reason for declining/skipping a habit."""

    __tablename__ = "decline_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    preset: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "sick", "busy", "tired", etc.

    def __repr__(self) -> str:
        return f"<DeclineNote(id={self.id}, preset={self.preset})>"
