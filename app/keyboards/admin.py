"""Admin dashboard keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🧪 Мои привычки", callback_data="admin_habits")],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )


def admin_user_actions_keyboard(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выдать подписку", callback_data=f"admin_grant:{tg_id}")],
            [InlineKeyboardButton(text="❌ Лишить подписки", callback_data=f"admin_revoke:{tg_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")],
        ]
    )


def admin_habits_keyboard(habits: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"admin_delete_habit:{hid}")]
        for hid, title in habits
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
