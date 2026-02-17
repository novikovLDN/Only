"""Admin dashboard keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t


def admin_main_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "admin_btn_users"), callback_data="admin_users")],
            [InlineKeyboardButton(text=t(lang, "admin_btn_stats"), callback_data="admin_stats")],
            [InlineKeyboardButton(text=t(lang, "admin_btn_my_habits"), callback_data="admin_habits")],
            [InlineKeyboardButton(text=t(lang, "admin_btn_delete_user"), callback_data="admin_delete_user")],
        ]
    )


def admin_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")]
        ]
    )


def admin_user_actions_keyboard(tg_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "admin_btn_grant"), callback_data=f"admin_grant:{tg_id}")],
            [InlineKeyboardButton(text=t(lang, "admin_btn_revoke"), callback_data=f"admin_revoke:{tg_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")],
        ]
    )


def admin_habits_keyboard(habits: list[tuple[int, str]], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"admin_delete_habit:{hid}")]
        for hid, title in habits
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
