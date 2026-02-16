"""User metrics — aggregated stats for achievement conditions."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserMetrics(Base):
    __tablename__ = "user_metrics"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_no_misses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    perfect_days_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_completions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completions_today: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completions_last_7_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completions_last_30_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    perfect_days_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    perfect_weeks_in_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    all_habits_completed_today: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    all_habits_completed_7_days: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    returned_after_miss_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    habits_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    habit_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    streak_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    habit_goal_increased: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    new_habit_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    habits_completed_daily: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invited_friends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    friends_with_7_day_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sync_with_friend_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_friends_30_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_categories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subscription_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
