"""Premium / subscription keyboard."""

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.premium import PREMIUM_TARIFFS
from app.services.discount_service import calculate_price_with_discount, is_discount_active
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


def crypto_network_menu(lang: str, tariff_code: str):
    """Network selection for crypto payment. Vertical list."""
    builder = InlineKeyboardBuilder()
    code = (lang or "ru")[:2].lower()
    lang = "ar" if code == "ar" else ("en" if code == "en" else "ru")
    networks = [
        ("network_trc20", "TRX-TRC20"),
        ("network_bep20", "BSC-BEP20"),
        ("network_erc20", "ETH-ERC20"),
        ("network_ton", "TON"),
    ]
    for key, net in networks:
        builder.button(text=t(lang, key), callback_data=f"crypto_network_{net}:{tariff_code}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"payment_method:{tariff_code}"))
    return builder.as_markup()


def premium_menu(lang: str, user=None):
    """Premium tariff selection — 1 button per row. Shows discounted prices if user has active discount."""
    builder = InlineKeyboardBuilder()
    code = (lang or "ru")[:2].lower()
    lang = "ar" if code == "ar" else ("en" if code == "en" else "ru")
    for tariff_code in ["1M", "3M", "6M", "12M"]:
        tinfo = PREMIUM_TARIFFS.get(tariff_code) or PREMIUM_TARIFFS["1M"]
        base_rub = tinfo["price_rub"]
        months = tinfo["months"]
        final_kopecks, discount_pct, original_rub = calculate_price_with_discount(user, base_rub)
        final_rub = int(final_kopecks / 100)
        if is_discount_active(user) and discount_pct > 0:
            if lang == "ru":
                label = f"{months} мес"
            elif lang == "en":
                label = f"{months} mo" if months == 1 else f"{months} mos"
            else:
                label = f"{months} شهر" if months == 1 else f"{months} أشهر"
            text = f"{label} — ~~{int(original_rub)} ₽~~ {final_rub} ₽"
        else:
            key = f"premium_{tariff_code.lower()}"
            text = t(lang, key)
        builder.button(text=text, callback_data=f"buy_tariff:{tariff_code}")

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main"))
    return builder.as_markup()
