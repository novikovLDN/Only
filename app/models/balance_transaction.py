"""
Balance transaction — аудит изменений баланса.

Каждое пополнение/списание — отдельная запись. Для аналитики и compliance.
"""

from decimal import Decimal
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BalanceTransaction(Base, TimestampMixin):
    """Immutable log of balance change."""

    __tablename__ = "balance_transactions"
    __table_args__ = (
        CheckConstraint(
            "type IN ('credit', 'debit', 'refund', 'referral_reward', 'subscription')",
            name="ck_balance_transactions_type",
        ),
        Index("ix_balance_transactions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Положительный для credit, отрицательный для debit",
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Ссылка на внешнюю сущность (referral_id и т.д.)",
    )

    def __repr__(self) -> str:
        return f"<BalanceTransaction(id={self.id}, user_id={self.user_id}, type={self.type})>"
