"""Keyboards — all exports."""

from .reminder import reminder_buttons, skip_reasons
from .main import main_menu
from .premium import premium_menu
from .settings import lang_select, settings_menu, timezone_keyboard, tz_select
from .habits import back_only, habits_list
from .profile import profile_keyboard

subscription_menu = premium_menu

__all__ = [
    "reminder_buttons",
    "skip_reasons",
    "main_menu",
    "subscription_menu",
    "premium_menu",
    "lang_select",
    "settings_menu",
    "tz_select",
    "timezone_keyboard",
    "back_only",
    "habits_list",
    "profile_keyboard",
]
