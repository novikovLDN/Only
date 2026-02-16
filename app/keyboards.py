"""Inline keyboards — attached to messages only."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import SUPPORT_URL, t


def lang_select(next_step: str = "tz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"lang_ru_{next_step}")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data=f"lang_en_{next_step}")],
    ])


def tz_select(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "tz_utc"), callback_data="tz_UTC")],
        [InlineKeyboardButton(text=t(lang, "tz_moscow"), callback_data="tz_Europe/Moscow")],
        [InlineKeyboardButton(text=t(lang, "tz_london"), callback_data="tz_Europe/London")],
        [InlineKeyboardButton(text=t(lang, "tz_dubai"), callback_data="tz_Asia/Dubai")],
        [InlineKeyboardButton(text=t(lang, "tz_almaty"), callback_data="tz_Asia/Almaty")],
        [InlineKeyboardButton(text=t(lang, "tz_ny"), callback_data="tz_America/New_York")],
        [InlineKeyboardButton(text=t(lang, "tz_other"), callback_data="tz_other")],
    ])


def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_add_habit"), callback_data="add_habit")],
        [InlineKeyboardButton(text=t(lang, "btn_my_habits"), callback_data="my_habits")],
        [InlineKeyboardButton(text=t(lang, "btn_profile"), callback_data="profile")],
        [InlineKeyboardButton(text=t(lang, "btn_settings"), callback_data="settings")],
        [InlineKeyboardButton(text=t(lang, "btn_subscription"), callback_data="subscription")],
        [InlineKeyboardButton(text=t(lang, "btn_support"), url=SUPPORT_URL)],
    ])


def reminder_buttons(lang: str, habit_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "reminder_done"), callback_data=f"done_{habit_id}"),
            InlineKeyboardButton(text=t(lang, "reminder_skip"), callback_data=f"skip_{habit_id}"),
        ],
    ])


def skip_reasons(lang: str, habit_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "skip_tired"), callback_data=f"skip_reason_{habit_id}_tired")],
        [InlineKeyboardButton(text=t(lang, "skip_sick"), callback_data=f"skip_reason_{habit_id}_sick")],
        [InlineKeyboardButton(text=t(lang, "skip_no_want"), callback_data=f"skip_reason_{habit_id}_no_want")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"skip_back_{habit_id}")],
    ])


def subscription_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "sub_buy_1"), callback_data="pay_1")],
        [InlineKeyboardButton(text=t(lang, "sub_buy_3"), callback_data="pay_3")],
        [InlineKeyboardButton(text=t(lang, "sub_buy_12"), callback_data="pay_12")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
    ])


def settings_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "settings_tz"), callback_data="settings_tz")],
        [InlineKeyboardButton(text=t(lang, "settings_lang"), callback_data="settings_lang")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
    ])


def profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "profile_missed"), callback_data="profile_missed")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")],
    ])


def back_only(lang: str, callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=callback_data)],
    ])


def habits_list(habits: list[tuple[int, str]], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=title, callback_data=f"habit_{hid}")] for hid, title in habits]
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
