"""Habits keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.habit_presets import HABIT_PRESETS
from app.texts import t

PAGE_SIZE = 6
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def build_presets_keyboard(lang: str, is_premium: bool, page: int = 0) -> InlineKeyboardMarkup:
    """Build preset habit buttons with RU/EN labels and premium lock. 2 cols x 3 rows, pagination."""
    lang = "en" if (lang or "").lower() == "en" else "ru"
    per_page = 6
    start = page * per_page
    end = start + per_page
    presets = HABIT_PRESETS[start:end]

    keyboard = []
    row = []
    for preset in presets:
        if not is_premium and preset["id"] > 3:
            text = f"🔒 {preset[lang]}"
            callback = "premium_required"
        else:
            text = preset[lang]
            callback = f"select_preset_{preset['id']}"
        row.append(InlineKeyboardButton(text=text, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton(text=t(lang, "habit_preset_prev"), callback_data=f"preset_page_{page - 1}"))
    if end < len(HABIT_PRESETS):
        pagination.append(InlineKeyboardButton(text=t(lang, "habit_preset_next"), callback_data=f"preset_page_{page + 1}"))
    if pagination:
        keyboard.append(pagination)

    custom_btn = InlineKeyboardButton(
        text=t(lang, "habit_custom") if is_premium else t(lang, "habit_custom_locked"),
        callback_data="preset_custom" if is_premium else "premium_required",
    )
    keyboard.append([custom_btn])
    keyboard.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_only(lang: str, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=callback_data)]
        ]
    )


def habits_list(habits: list[tuple[int, str]], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=title, callback_data=f"habit_{hid}")]
        for hid, title in habits
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def weekdays_keyboard(selected: list[int], lang: str) -> InlineKeyboardMarkup:
    row1 = []
    for i in range(7):
        label = WEEKDAYS[i] + (" ✅" if i in selected else "")
        row1.append(InlineKeyboardButton(text=label, callback_data=f"wd_{i}"))
    rows = [row1]
    rows.append([InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="days_ok")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_keyboard(selected: list[str], lang: str) -> InlineKeyboardMarkup:
    hours = [f"{h:02d}:00" for h in range(24)]
    rows = []
    for i in range(0, 24, 6):
        row = []
        for h in range(i, min(i + 6, 24)):
            t_slot = f"{h:02d}:00"
            label = t_slot + (" ✅" if t_slot in selected else "")
            row.append(InlineKeyboardButton(text=label, callback_data=f"tm_{t_slot}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="time_ok")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="habit_confirm_ok")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
            [InlineKeyboardButton(text=t(lang, "habit_cancel"), callback_data="habit_cancel")],
        ]
    )


def edit_habit_menu(habit_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "edit_days_btn"), callback_data=f"edit_days:{habit_id}")],
            [InlineKeyboardButton(text=t(lang, "edit_time_btn"), callback_data=f"edit_time:{habit_id}")],
            [InlineKeyboardButton(text=t(lang, "delete_btn"), callback_data=f"habit_delete:{habit_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="edit_habits")],
        ]
    )


def edit_weekdays_keyboard(habit_id: int, selected: list[int], lang: str) -> InlineKeyboardMarkup:
    row1 = []
    for i in range(7):
        label = WEEKDAYS[i] + (" ✅" if i in selected else "")
        row1.append(InlineKeyboardButton(text=label, callback_data=f"edit_wd:{habit_id}:{i}"))
    rows = [row1]
    rows.append([InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data=f"edit_days_ok:{habit_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"habit_{habit_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_time_keyboard_for_habit(habit_id: int, selected: list[str], lang: str) -> InlineKeyboardMarkup:
    hours = [f"{h:02d}:00" for h in range(24)]
    rows = []
    for i in range(0, 24, 6):
        row = []
        for h in range(i, min(i + 6, 24)):
            t_slot = f"{h:02d}:00"
            label = t_slot + (" ✅" if t_slot in selected else "")
            row.append(InlineKeyboardButton(text=label, callback_data=f"edit_tm:{habit_id}:{t_slot}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data=f"edit_time_ok:{habit_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"habit_{habit_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
