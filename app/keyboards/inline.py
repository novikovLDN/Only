"""Inline keyboards — ONLY InlineKeyboardMarkup, emoji on all buttons."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.i18n import get_presets, get_weekdays

SUPPORT_URL = "https://t.me/asc_support"
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
        [InlineKeyboardButton(text=t("btn.subscribe"), callback_data="to_subscription")],
        [InlineKeyboardButton(text=t("btn.settings"), callback_data="settings")],
        [InlineKeyboardButton(text=t("btn.support"), url=SUPPORT_URL)],
    ])


def back_only(t, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.back"), callback_data=callback_data)],
    ])


def build_habit_grid(
    t,
    habits: list[tuple[int, str]],
    selected_ids: set[int],
    page: int,
    page_size: int = 6,
    is_premium: bool = True,
) -> InlineKeyboardMarkup:
    """2 cols x 3 rows, 6 per page. Left column first, row-by-row."""
    total_pages = max(1, (len(habits) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    chunk = habits[start : start + page_size]
    rows = []
    for i in range(0, len(chunk), 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx >= len(chunk):
                break
            hid, title = chunk[idx]
            locked = not is_premium and hid >= HABIT_PRESETS_LIMIT_FREE
            if locked:
                row.append(InlineKeyboardButton(text=f"🔒 {title}", callback_data="premium"))
            else:
                mark = "✅ " if hid in selected_ids else "⬜ "
                row.append(InlineKeyboardButton(text=f"{mark}{title}", callback_data=f"habit_toggle:{hid}"))
        if row:
            rows.append(row)
    if total_pages > 1:
        pagination = []
        if page > 0:
            pagination.append(InlineKeyboardButton(text=t("preset.page_prev"), callback_data=f"habit_page:{page - 1}"))
        pagination.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pagination.append(InlineKeyboardButton(text=t("preset.page_next"), callback_data=f"habit_page:{page + 1}"))
        rows.append(pagination)
    custom_cb = "custom_habit" if is_premium else "premium"
    rows.append([InlineKeyboardButton(text=t("btn.add_custom"), callback_data=custom_cb)])
    rows.append([
        InlineKeyboardButton(text=t("preset.nav_back"), callback_data="habit_back"),
        InlineKeyboardButton(text=t("preset.nav_next"), callback_data="habit_next"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def presets_page(t, lang: str, page: int, selected: set[int], is_premium: bool) -> InlineKeyboardMarkup:
    presets = get_presets(lang)
    habits = list(enumerate(presets))
    return build_habit_grid(t, habits, selected, page, 6, is_premium)


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
    rows.append([
        InlineKeyboardButton(text=t("btn.back"), callback_data=back_cb),
        InlineKeyboardButton(text=t("btn.next"), callback_data="days_done"),
    ])
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
    rows.append([
        InlineKeyboardButton(text=t("btn.back"), callback_data=back_callback),
        InlineKeyboardButton(text=t("btn.done"), callback_data=done_callback),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_menu(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("settings.my_profile"), callback_data="settings_profile")],
        [InlineKeyboardButton(text=t("btn.support"), url=SUPPORT_URL)],
        [InlineKeyboardButton(text=t("settings.change_language"), callback_data="settings_lang")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")],
    ])


def language_select_with_back(t, back_callback: str = "back_main", return_to: str | None = None) -> InlineKeyboardMarkup:
    suffix = f"_{return_to}" if return_to else ""
    rows = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"lang_ru{suffix}")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data=f"lang_en{suffix}")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_menu(t, has_subscription: bool) -> InlineKeyboardMarkup:
    rows = []
    rows.append([InlineKeyboardButton(text=t("progress.btn"), callback_data="profile_progress")])
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
    rows.append([InlineKeyboardButton(text=t("btn.support"), url=SUPPORT_URL)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_method_select(t, tariff: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("subscription.cryptobot"), callback_data=f"pay_cryptobot_{tariff}")],
        [InlineKeyboardButton(text=t("subscription.bank_card"), callback_data=f"pay_card_{tariff}")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="to_subscription")],
        [InlineKeyboardButton(text=t("btn.support"), url=SUPPORT_URL)],
    ])


def buy_subscription_only(t) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("premium.buy"), callback_data="to_subscription")],
        [InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")],
        [InlineKeyboardButton(text=t("btn.support"), url=SUPPORT_URL)],
    ])


def progress_menu(t, has_missed: bool = False) -> InlineKeyboardMarkup:
    rows = []
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="settings_profile")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_habits_list(t, habits: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Inline list of habits for editing."""
    rows = [[InlineKeyboardButton(text=title, callback_data=f"edit_habit:{hid}")] for hid, title in habits]
    rows.append([InlineKeyboardButton(text=t("btn.back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def habit_confirm_decline(t, log_id: int) -> InlineKeyboardMarkup:
    """Confirm/Decline buttons for habit reminder."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn.confirm"), callback_data=f"habit_confirm:{log_id}"),
            InlineKeyboardButton(text=t("btn.decline"), callback_data=f"habit_decline:{log_id}"),
        ],
    ])


def decline_reasons(t, log_id: int) -> InlineKeyboardMarkup:
    """Decline reason buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("decline.reason_tired"), callback_data=f"habit_decline_tired:{log_id}")],
        [InlineKeyboardButton(text=t("decline.reason_sick"), callback_data=f"habit_decline_sick:{log_id}")],
        [InlineKeyboardButton(text=t("decline.reason_no_want"), callback_data=f"habit_decline_no_want:{log_id}")],
        [InlineKeyboardButton(text=t("decline.back"), callback_data=f"habit_decline_back:{log_id}")],
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
