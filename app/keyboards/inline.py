"""Inline keyboards — ONLY InlineKeyboardMarkup, emoji on all buttons."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.i18n import get_presets, get_weekdays
from app.core.constants import HABIT_PRESETS_LIMIT_FREE
from app.core.enums import Tariff, TARIFF_PRICES_RUB

TIME_EMOJI = [
    "🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚",
    "🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚",
]


def language_select() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
    ])


def main_menu(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.add_habit"), callback_data="add_habit")],
        [InlineKeyboardButton(text=t("btn.edit_habits"), callback_data="edit_habits")],
        [InlineKeyboardButton(text=t("btn.loyalty"), callback_data="loyalty")],
        [InlineKeyboardButton(text=t("btn.settings"), callback_data="settings")],
    ])


def back_only(t, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.back"), callback_data=callback_data)],
    ])


def presets_page(t, lang: str, page: int, selected: set[int], is_premium: bool) -> InlineKeyboardMarkup:
    presets = get_presets(lang)
    per_page = 6
    total_pages = (len(presets) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(presets))
    rows = []
    for i in range(start, end):
        locked = not is_premium and i >= HABIT_PRESETS_LIMIT_FREE
        mark = "🟢 " if i in selected else "⚪ "
        if locked:
            rows.append([InlineKeyboardButton(text=f"🔒 {presets[i]}", callback_data="premium")])
        else:
            rows.append([InlineKeyboardButton(text=f"{mark}{presets[i]}", callback_data=f"preset_toggle_{i}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t("btn.prev"), callback_data=f"preset_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=t("btn.next"), callback_data=f"preset_page_{page + 1}"))
    if nav:
        rows.append(nav)

    custom_cb = "custom_habit" if is_premium else "premium"
    rows.append([InlineKeyboardButton(text=t("btn.add_custom"), callback_data=custom_cb)])
    rows.append([InlineKeyboardButton(text=t("btn.done"), callback_data="preset_done")])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def weekdays_select(t, selected: set[int], lang: str = "en", callback_prefix: str = "day", back_cb: str = "back_main") -> InlineKeyboardMarkup:
    weekdays = get_weekdays(lang)
    rows = []
    row = []
    for i, wd in enumerate(weekdays):
        mark = "🟢 " if i in selected else "⚪ "
        row.append(InlineKeyboardButton(text=f"{mark}{wd}", callback_data=f"{callback_prefix}_{i}"))
        if len(row) >= 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn.next"), callback_data="days_done")])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_select(t, selected: set[int], callback_prefix: str = "time", done_callback: str = "times_done", back_callback: str = "back_main") -> InlineKeyboardMarkup:
    rows = []
    row = []
    for h in range(24):
        emoji = TIME_EMOJI[h]
        mark = "🟢 " if h in selected else "⚪ "
        row.append(InlineKeyboardButton(text=f"{mark}{emoji} {h:02d}:00", callback_data=f"{callback_prefix}_{h}"))
        if len(row) >= 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn.done"), callback_data=done_callback)])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_menu(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("settings.my_profile"), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("settings.support"), callback_data="support")],
        [InlineKeyboardButton(text=t("settings.change_language"), callback_data="settings_lang")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")],
    ])


def language_select_with_back(t, back_callback: str = "back_main") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_menu(t, has_subscription: bool) -> InlineKeyboardMarkup:
    rows = []
    if not has_subscription:
        rows.append([InlineKeyboardButton(text=t("profile.buy"), callback_data="to_subscription")])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def loyalty_menu(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("loyalty.share"), callback_data="share_link")],
        [InlineKeyboardButton(text=t("loyalty.details"), callback_data="loyalty_details")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")],
    ])


def tariff_select(t) -> InlineKeyboardMarkup:
    keys = {"1_month": "subscription.tariff_1m", "3_months": "subscription.tariff_3m", "6_months": "subscription.tariff_6m", "12_months": "subscription.tariff_12m"}
    rows = []
    for tariff, price in TARIFF_PRICES_RUB.items():
        key = keys.get(tariff.value, "subscription.tariff_1m")
        label = t(key, price=price)
        rows.append([InlineKeyboardButton(text=label, callback_data=f"tariff_{tariff.value}")])
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_method_select(t, tariff: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("subscription.cryptobot"), callback_data=f"pay_cryptobot_{tariff}")],
        [InlineKeyboardButton(text=t("subscription.bank_card"), callback_data=f"pay_card_{tariff}")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="to_subscription")],
    ])


def buy_subscription_only(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("premium.buy"), callback_data="to_subscription")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")],
    ])


def edit_habit_detail(t, habit_id: int, lang: str = "en", current_days: set[int] | None = None) -> InlineKeyboardMarkup:
    weekdays = get_weekdays(lang)
    current_days = current_days or set()
    rows = []
    row = []
    for i, wd in enumerate(weekdays):
        mark = "🟢" if i in current_days else "⚪"
        row.append(InlineKeyboardButton(text=f"{mark} {wd}", callback_data=f"editday_{habit_id}_{i}"))
        if len(row) >= 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.extend([
        [InlineKeyboardButton(text=t("habit.change_time"), callback_data=f"chtime_{habit_id}")],
        [InlineKeyboardButton(text=t("habit.delete"), callback_data=f"del_habit_{habit_id}")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_edit")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
