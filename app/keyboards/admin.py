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
            [InlineKeyboardButton(text=t(lang, "admin_btn_discount"), callback_data=f"admin_discount:{tg_id}")],
            [InlineKeyboardButton(text=t(lang, "admin_btn_delete_user"), callback_data=f"admin_delete_this:{tg_id}")],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")],
        ]
    )


def admin_discount_percent_keyboard(tg_id: int, lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"{p}%", callback_data=f"admin_discount_pct:{tg_id}:{p}")] for p in [10, 15, 20, 25, 30, 50]]
    rows.append([InlineKeyboardButton(text=t(lang, "admin_discount_manual"), callback_data=f"admin_discount_pct_manual:{tg_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_discount_duration_keyboard(tg_id: int, percent: int, lang: str) -> InlineKeyboardMarkup:
    opts = [(1, "admin_dur_1d"), (3, "admin_dur_3d"), (7, "admin_dur_7d"), (14, "admin_dur_14d"), (30, "admin_dur_30d"), (90, "admin_dur_90d")]
    rows = [[InlineKeyboardButton(text=t(lang, k), callback_data=f"admin_discount_dur:{tg_id}:{percent}:{d}")] for d, k in opts]
    rows.append([InlineKeyboardButton(text=t(lang, "admin_discount_manual"), callback_data=f"admin_discount_dur_manual:{tg_id}:{percent}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"admin_discount:{tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_discount_confirm_keyboard(tg_id: int, percent: int, days: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "admin_discount_confirm_btn"), callback_data=f"admin_discount_confirm:{tg_id}:{percent}:{days}")],
            [InlineKeyboardButton(text=t(lang, "admin_discount_cancel_btn"), callback_data="admin_back")],
        ]
    )


def admin_habits_keyboard(habits: list[tuple[int, str]], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"admin_delete_habit:{hid}")]
        for hid, title in habits
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
