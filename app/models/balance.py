"""
Balance model — текущий баланс пользователя.

Денормализация для производительности. Audit trail — balance_transactions.
"""

from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Balance(Base, TimestampMixin):
    """User balance (one row per user)."""

    __tablename__ = "balances"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_balances_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")

    user = relationship("User", back_populates="balances")

    def __repr__(self) -> str:
        return f"<Balance(user_id={self.user_id}, amount={self.amount})>"
