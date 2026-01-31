"""
Subscription model.

payment_id — ссылка на платёж, активировавший подписку (nullable при trial).
Даты в UTC (DateTime timezone=True).
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Subscription(Base, TimestampMixin):
    """User subscription record."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "tier IN ('trial', 'free', 'premium')",
            name="ck_subscriptions_tier",
        ),
        Index("ix_subscriptions_user_active", "user_id", "is_active"),
        Index("ix_subscriptions_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        comment="Платёж, активировавший подписку",
    )
    auto_renew_from_balance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Автопродление с баланса при истечении",
    )
    last_renewal_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последняя попытка автопродления (для retry cooldown)",
    )

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier})>"
