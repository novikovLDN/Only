"""Habits keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.habit_presets import HABIT_PRESETS
from app.texts import t

PAGE_SIZE = 6
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
# Fixed-width 2–3 char labels for stable 2-column grid (all devices)
WEEKDAYS_RU = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
WEEKDAYS_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
WEEKDAYS_AR = ["إثنين", "ثلاثاء", "أربعاء", "خميس", "جمعة", "سبت", "أحد"]


def _norm_lang(lang: str) -> str:
    code = (lang or "ru")[:2].lower()
    return "ar" if code == "ar" else ("en" if code == "en" else "ru")


def build_presets_keyboard(lang: str, is_premium: bool, page: int = 0) -> InlineKeyboardMarkup:
    """Build preset habit buttons with RU/EN/AR labels and premium lock. 2 cols x 3 rows, pagination."""
    lang = _norm_lang(lang)
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
    """2 columns × 4 rows for stable rendering on all devices."""
    code = _norm_lang(lang)
    labels = WEEKDAYS_AR if code == "ar" else (WEEKDAYS_EN if code == "en" else WEEKDAYS_RU)
    selected_set = set(selected)
    kb = []
    for i in range(0, 8, 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < 7:
                is_active = idx in selected_set
                prefix = "🟢 " if is_active else "⚪ "
                row.append(
                    InlineKeyboardButton(
                        text=f"{prefix}{labels[idx]}",
                        callback_data=f"wd_{idx}",
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(text="⬜", callback_data="noop")
                )
        kb.append(row)
    kb.append([
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main"),
        InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="days_ok"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def time_keyboard(selected: list[str], lang: str) -> InlineKeyboardMarkup:
    """2 columns × 12 rows for stable rendering on all devices."""
    selected_set = set(selected)
    times = [f"{h:02d}:00" for h in range(24)]
    kb = []
    for i in range(0, 24, 2):
        row = []
        for j in range(2):
            t_slot = times[i + j]
            is_active = t_slot in selected_set
            prefix = "🟢 " if is_active else "⚪ "
            row.append(
                InlineKeyboardButton(
                    text=f"{prefix}{t_slot}",
                    callback_data=f"tm_{t_slot}",
                )
            )
        kb.append(row)
    kb.append([
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main"),
        InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="time_ok"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main"),
                InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data="habit_confirm_ok"),
            ],
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
    """2 columns × 4 rows for stable rendering on all devices."""
    code = _norm_lang(lang)
    labels = WEEKDAYS_AR if code == "ar" else (WEEKDAYS_EN if code == "en" else WEEKDAYS_RU)
    selected_set = set(selected)
    kb = []
    for i in range(0, 8, 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < 7:
                is_active = idx in selected_set
                prefix = "🟢 " if is_active else "⚪ "
                row.append(
                    InlineKeyboardButton(
                        text=f"{prefix}{labels[idx]}",
                        callback_data=f"edit_wd:{habit_id}:{idx}",
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(text="⬜", callback_data="noop")
                )
        kb.append(row)
    kb.append([
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"habit_{habit_id}"),
        InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data=f"edit_days_ok:{habit_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def edit_time_keyboard_for_habit(habit_id: int, selected: list[str], lang: str) -> InlineKeyboardMarkup:
    """2 columns × 12 rows for stable rendering on all devices."""
    selected_set = set(selected)
    times = [f"{h:02d}:00" for h in range(24)]
    kb = []
    for i in range(0, 24, 2):
        row = []
        for j in range(2):
            t_slot = times[i + j]
            is_active = t_slot in selected_set
            prefix = "🟢 " if is_active else "⚪ "
            row.append(
                InlineKeyboardButton(
                    text=f"{prefix}{t_slot}",
                    callback_data=f"edit_tm:{habit_id}:{t_slot}",
                )
            )
        kb.append(row)
    kb.append([
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"habit_{habit_id}"),
        InlineKeyboardButton(text=t(lang, "habit_confirm_preset"), callback_data=f"edit_time_ok:{habit_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)
