"""Centralized tariff config for Telegram Invoice / YooKassa."""

TARIFFS = {
    "1_month": {
        "title": "1 Month",
        "price": 259,
        "days": 30,
    },
    "3_months": {
        "title": "3 Months",
        "price": 599,
        "days": 90,
    },
    "6_months": {
        "title": "6 Months",
        "price": 999,
        "days": 180,
    },
    "12_months": {
        "title": "12 Months",
        "price": 1699,
        "days": 365,
    },
}

CURRENCY = "RUB"
