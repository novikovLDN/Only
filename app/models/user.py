"""
User model.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.constants import UserTier
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    tier: Mapped[str] = mapped_column(String(20), nullable=False, default=UserTier.TRIAL)
    trial_ends_at: Mapped[datetime | None] = mapped_column(nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=True, index=True)
    referred_by_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    balances = relationship("Balance", back_populates="user", cascade="all, delete-orphan")
    referrals_given = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        back_populates="referrer",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, tier={self.tier})>"
