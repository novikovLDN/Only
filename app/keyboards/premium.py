"""Premium / subscription keyboard."""

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.texts import t


def payment_method_menu(lang: str, tariff_code: str):
    """Card / Crypto selection for chosen tariff."""
    builder = InlineKeyboardBuilder()
    code = (lang or "ru")[:2].lower()
    lang = "ar" if code == "ar" else ("en" if code == "en" else "ru")
    builder.button(text=t(lang, "pay_card"), callback_data=f"pay_card:{tariff_code}")
    builder.button(text=t(lang, "pay_crypto"), callback_data=f"pay_crypto:{tariff_code}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="premium"))
    return builder.as_markup()


def premium_menu(lang: str):
    """Premium tariff selection — 1 button per row for consistent mobile display."""
    builder = InlineKeyboardBuilder()
    code = (lang or "ru")[:2].lower()
    lang = "ar" if code == "ar" else ("en" if code == "en" else "ru")

    for code in ["1M", "3M", "6M", "12M"]:
        key = f"premium_{code.lower()}"  # premium_1m, premium_3m, etc
        builder.button(
            text=t(lang, key),
            callback_data=f"buy_tariff:{code}",
        )

    builder.adjust(1)  # One button per row
    builder.row(
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main"),
    )

    return builder.as_markup()
