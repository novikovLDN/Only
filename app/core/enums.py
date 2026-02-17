"""Enums and constants."""

from enum import Enum


class Language(str, Enum):
    RU = "ru"
    EN = "en"
    AR = "ar"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tariff(str, Enum):
    MONTH_1 = "1_month"
    MONTH_3 = "3_months"
    MONTH_6 = "6_months"
    MONTH_12 = "12_months"


TARIFF_DAYS = {
    Tariff.MONTH_1: 30,
    Tariff.MONTH_3: 90,
    Tariff.MONTH_6: 180,
    Tariff.MONTH_12: 365,
}

TARIFF_PRICES_RUB = {
    Tariff.MONTH_1: 259,
    Tariff.MONTH_3: 599,
    Tariff.MONTH_6: 999,
    Tariff.MONTH_12: 1699,
}
