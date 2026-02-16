"""Referral — referrer/referred with reward tracking."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    referral_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reward_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_sent")
    referral_user: Mapped["User"] = relationship(
        "User", foreign_keys=[referral_user_id], back_populates="referrals_received"
    )
