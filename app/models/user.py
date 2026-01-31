"""
User model.

Primary key: id = telegram_id для упрощения связей.
Для аналитики: created_at индексирован.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.constants import UserTier
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Telegram user."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "tier IN ('trial', 'free', 'premium')",
            name="ck_users_tier",
        ),
        Index("ix_users_created_at", "created_at"),  # Аналитика по когортам
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        comment="Telegram user id, используется как PK",
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Дубликат id для явности; unique для быстрого поиска",
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserTier.TRIAL,
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Окончание trial; NULL если не trial",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        comment="IANA timezone для напоминаний",
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referral_code: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        nullable=True,
        index=True,
        comment="Уникальный код для реферальной ссылки",
    )
    referred_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID пользователя-реферера",
    )
    device_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Для антифрода (multi-account)",
    )
    last_inactivity_reminder_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последнее напоминание о неактивности",
    )
    last_streak_milestone: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Последний отпразднованный streak (7, 14, 30...)",
    )

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
