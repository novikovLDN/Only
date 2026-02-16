"""User model."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, default="ru")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    premium_reward_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    habits: Mapped[list["Habit"]] = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    habit_logs: Mapped[list["HabitLog"]] = relationship("HabitLog", back_populates="user", cascade="all, delete-orphan")
    referrals_sent: Mapped[list["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.referrer_id", back_populates="referrer"
    )
    referrals_received: Mapped[list["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.referral_user_id", back_populates="referral_user"
    )
