"""
Keyboards для FSM создания привычки и decline.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.fsm.constants import DECLINE_PRESETS, HABIT_TEMPLATES, TIME_SLOTS, WEEKDAYS
from app.texts import HABIT_DECLINE_SKIP_BTN


def habit_template_keyboard() -> InlineKeyboardMarkup:
    """Шаблоны + «Своя привычка»."""
    buttons = []
    for tid, (name, emoji) in HABIT_TEMPLATES.items():
        buttons.append([
            InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"habit_tpl:{tid}"),
        ])
    buttons.append([InlineKeyboardButton(text="✏️ Своя привычка", callback_data="habit_tpl:custom")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def habit_days_keyboard(selected: list[int]) -> InlineKeyboardMarkup:
    """Multi-select дней. selected = [0,1,2] для Пн,Вт,Ср."""
    buttons = []
    row = []
    for i, label in enumerate(WEEKDAYS):
        prefix = "✅" if i in selected else "⬜"
        row.append(InlineKeyboardButton(
            text=f"{prefix}{label}",
            callback_data=f"habit_day:{i}",
        ))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text="➡️ Дальше", callback_data="habit_days_ok"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def habit_time_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    """Multi-select времени."""
    buttons = []
    row = []
    for t in TIME_SLOTS:
        prefix = "✅" if t in selected else "⬜"
        row.append(InlineKeyboardButton(
            text=f"{prefix}{t}",
            callback_data=f"habit_time:{t}",
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text="➡️ Дальше", callback_data="habit_time_ok"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def habit_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение создания."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="habit_confirm:yes"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="habit_confirm:edit"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="habit_confirm:no")],
        ]
    )


def habit_decline_presets_keyboard() -> InlineKeyboardMarkup:
    """Пресеты для decline + пропустить."""
    buttons = []
    for label, preset in DECLINE_PRESETS:
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"habit_decline_preset:{preset}")])
    buttons.append([InlineKeyboardButton(text=HABIT_DECLINE_SKIP_BTN, callback_data="habit_decline_preset:skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
