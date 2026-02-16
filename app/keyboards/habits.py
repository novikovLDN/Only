"""Habits keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t

PAGE_SIZE = 6
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


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


def presets_grid(presets: list[str], page: int, lang: str, is_premium: bool) -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    chunk = presets[start : start + PAGE_SIZE]
    left_column = chunk[:3]
    right_column = chunk[3:6]
    rows = []
    for i in range(3):
        row = []
        if i < len(left_column):
            idx = start + i
            title = left_column[i]
            if is_premium or idx < 3:
                row.append(InlineKeyboardButton(text=title, callback_data=f"preset_{idx}"))
            else:
                row.append(InlineKeyboardButton(text=f"{title} 🔒", callback_data="premium_required"))
        if i < len(right_column):
            idx = start + i + 3
            title = right_column[i]
            if is_premium or idx < 3:
                row.append(InlineKeyboardButton(text=title, callback_data=f"preset_{idx}"))
            else:
                row.append(InlineKeyboardButton(text=f"{title} 🔒", callback_data="premium_required"))
        if row:
            rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t(lang, "habit_preset_prev"), callback_data="preset_prev"))
    if start + PAGE_SIZE < len(presets):
        nav.append(InlineKeyboardButton(text=t(lang, "habit_preset_next"), callback_data="preset_next"))
    if nav:
        rows.append(nav)
    if is_premium:
        rows.append([InlineKeyboardButton(text=t(lang, "habit_custom"), callback_data="preset_custom")])
    else:
        rows.append([
            InlineKeyboardButton(text=t(lang, "habit_custom_locked"), callback_data="premium_required")
        ])
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
            [InlineKeyboardButton(text="Изменить дни", callback_data=f"edit_days:{habit_id}")],
            [InlineKeyboardButton(text="Изменить время", callback_data=f"edit_time:{habit_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"habit_delete:{habit_id}")],
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
