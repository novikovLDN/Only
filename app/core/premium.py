"""Premium tariff config — prices, months, discounts."""

PREMIUM_TARIFFS = {
    "1M": {
        "months": 1,
        "price_rub": 99,
        "discount": None,
    },
    "3M": {
        "months": 3,
        "price_rub": 269,
        "discount": "-10%",
    },
    "6M": {
        "months": 6,
        "price_rub": 499,
        "discount": "-15%",
    },
    "12M": {
        "months": 12,
        "price_rub": 829,
        "discount": "-30%",
    },
}
