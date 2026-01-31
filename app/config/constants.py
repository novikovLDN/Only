"""
Application constants.
"""

from enum import StrEnum


class UserTier(StrEnum):
    """User subscription tier."""

    TRIAL = "trial"
    FREE = "free"
    PREMIUM = "premium"


class HabitScheduleType(StrEnum):
    """Habit reminder schedule type."""

    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class PaymentProvider(StrEnum):
    """Payment provider identifier."""

    YOOKASSA = "yookassa"
    TELEGRAM_STARS = "telegram_stars"
    CRYPTOBOT = "cryptobot"


class PaymentType(StrEnum):
    """Type of payment."""

    BALANCE_TOPUP = "balance_topup"
    SUBSCRIPTION = "subscription"


class AlertSeverity(StrEnum):
    """Severity for monitoring alerts."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# Trial lifecycle notification offsets (hours from trial start/end)
TRIAL_NOTIFICATION_OFFSETS = [
    36,  # +36h after start
    90,  # +90h mid-trial
]

TRIAL_EXPIRY_OFFSETS = [
    -24,  # -24h before expiry
    -3,   # -3h before expiry
]

SUBSCRIPTION_EXPIRY_OFFSETS = [
    -72,  # -3 days
    -24,  # -24h
    -3,   # -3h
]

# Subscription plans (days)
SUBSCRIPTION_PLANS = {
    "monthly": 30,
    "yearly": 365,
}
