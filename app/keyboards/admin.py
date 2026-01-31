"""
Admin panel inline keyboards.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CALLBACK_PREFIX = "admin:"

SECTION_SYSTEM = "system"
SECTION_USERS = "users"
SECTION_SUBS = "subs"
SECTION_FINANCE = "finance"
SECTION_ANALYTICS = "analytics"
SECTION_ERRORS = "errors"
SECTION_BACK = "back"


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Main admin menu — sections."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖥 System",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_SYSTEM}",
                ),
                InlineKeyboardButton(
                    text="👥 Users",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_USERS}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📅 Subscriptions",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_SUBS}",
                ),
                InlineKeyboardButton(
                    text="💰 Finance",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_FINANCE}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📈 Analytics",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_ANALYTICS}",
                ),
                InlineKeyboardButton(
                    text="⚠️ Errors",
                    callback_data=f"{CALLBACK_PREFIX}{SECTION_ERRORS}",
                ),
            ],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    """Back to main admin menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Back", callback_data=f"{CALLBACK_PREFIX}{SECTION_BACK}")],
        ]
    )
