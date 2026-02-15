"""Reply keyboards for ALL navigation — mobile-friendly, always visible."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.keyboards.base import build_menu
from app.utils.i18n import get_presets, get_weekdays

SUPPORT_URL = "https://t.me/asc_support"
from app.core.constants import HABIT_PRESETS_LIMIT_FREE
from app.core.enums import Tariff, TARIFF_PRICES_RUB

TIME_EMOJI = [
    "🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚",
] * 2


def main_menu(t) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("btn.add_habit"), t("btn.edit_habits")],
        [t("btn.loyalty"), t("btn.subscribe")],
        [t("btn.settings"), t("btn.support")],
        [t("btn.back")],
    ], placeholder=t("main.action_prompt"))


def language_select() -> ReplyKeyboardMarkup:
    return build_menu([
        ["🇷🇺 Русский"],
        ["🇺🇸 English"],
    ])


def language_select_with_back(t) -> ReplyKeyboardMarkup:
    return build_menu([
        ["🇷🇺 Русский"],
        ["🇺🇸 English"],
        [t("btn.back")],
    ])


def settings_menu(t) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("settings.my_profile")],
        [t("settings.change_language")],
        [t("btn.support")],
        [t("btn.back")],
    ])


def presets_page(t, lang: str, page: int, is_premium: bool) -> ReplyKeyboardMarkup:
    presets = get_presets(lang)
    page_size = 6
    total_pages = max(1, (len(presets) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    chunk = presets[start : start + page_size]
    rows = []
    for i in range(0, len(chunk), 2):
        row = []
        for j in range(2):
            idx = start + i + j
            if idx >= len(presets):
                break
            title = presets[idx]
            if not is_premium and idx >= HABIT_PRESETS_LIMIT_FREE:
                title = f"🔒 {title}"
            row.append(title)
        if row:
            rows.append(row)
    rows.append([t("btn.add_custom")])
    rows.append([t("preset.nav_back"), t("preset.nav_next")])
    return build_menu(rows, placeholder=t("preset.choose_title"))


def weekdays_select(t, lang: str) -> ReplyKeyboardMarkup:
    weekdays = get_weekdays(lang)
    return build_menu([
        weekdays[:4],
        weekdays[4:],
        [t("btn.done")],
        [t("btn.back")],
    ])


def times_select(t) -> ReplyKeyboardMarkup:
    rows = []
    for h in range(24):
        label = f"{TIME_EMOJI[h]} {h:02d}:00"
        if h % 6 == 0:
            rows.append([])
        rows[-1].append(label)
    rows.append([t("btn.done")])
    rows.append([t("btn.back")])
    return build_menu(rows)


def tariff_select(t) -> ReplyKeyboardMarkup:
    keys = {"1_month": "subscription.tariff_1m", "3_months": "subscription.tariff_3m",
            "6_months": "subscription.tariff_6m", "12_months": "subscription.tariff_12m"}
    labels = [t(keys.get(tariff.value, "subscription.tariff_1m"), price=TARIFF_PRICES_RUB[tariff])
              for tariff in Tariff]
    return build_menu(
        [[l] for l in labels] + [[t("btn.back")], [t("btn.support")]],
        placeholder=t("subscription.choose_tariff"),
    )


def payment_method_select(t, tariff: str) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("subscription.cryptobot")],
        [t("subscription.bank_card")],
        [t("btn.back")],
        [t("btn.support")],
    ], placeholder=t("subscription.choose_payment"))


def buy_subscription_only(t) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("premium.buy")],
        [t("btn.back")],
        [t("btn.support")],
    ])


def profile_menu(t, has_subscription: bool) -> ReplyKeyboardMarkup:
    rows = [[t("progress.btn")]]
    if not has_subscription:
        rows.append([t("profile.buy")])
    rows.append([t("btn.back")])
    return build_menu(rows)


def progress_menu(t, has_missed: bool) -> ReplyKeyboardMarkup:
    rows = []
    if has_missed:
        rows.append([t("progress.my_missed")])
    rows.append([t("btn.back")])
    return build_menu(rows)


def loyalty_menu(t) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("loyalty.share")],
        [t("loyalty.details")],
        [t("btn.back")],
    ])


def edit_habits_list(t, habit_titles: list[str]) -> ReplyKeyboardMarkup:
    rows = [[h] for h in habit_titles]
    rows.append([t("btn.back")])
    return build_menu(rows)


def edit_habit_detail(t) -> ReplyKeyboardMarkup:
    return build_menu([
        [t("habit.change_time")],
        [t("habit.delete")],
        [t("btn.back")],
    ])


def edit_habit_days(t, lang: str) -> ReplyKeyboardMarkup:
    weekdays = get_weekdays(lang)
    return build_menu([
        weekdays[:4],
        weekdays[4:],
        [t("btn.done")],
        [t("btn.back")],
    ])


def back_only(t) -> ReplyKeyboardMarkup:
    return build_menu([[t("btn.back")]])


def habit_confirm_decline(t) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn.confirm")),
                KeyboardButton(text=t("btn.decline")),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def decline_reasons(t) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("decline.reason_tired"))],
            [KeyboardButton(text=t("decline.reason_sick"))],
            [KeyboardButton(text=t("decline.reason_no_want"))],
            [KeyboardButton(text=t("decline.back"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
