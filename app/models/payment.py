"""
Payment model.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config.constants import PaymentProvider, PaymentType
from app.models.base import Base, TimestampMixin


class Payment(Base, TimestampMixin):
    """Payment record — balance top-up or subscription."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Extra provider data
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, provider={self.provider}, status={self.status})>"
