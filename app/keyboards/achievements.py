"""Achievements keyboard — 2 per row, 8 per page, pagination."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.texts import t

PER_PAGE = 8


def achievements_keyboard(
    achievements: list[tuple[int, str, bool]],
    page: int,
    lang: str,
    total: int,
) -> InlineKeyboardMarkup:
    """Build 2-per-row grid. achievements: [(id, name, unlocked), ...]."""
    start = page * PER_PAGE
    chunk = achievements[start : start + PER_PAGE]
    rows = []
    for i in range(0, len(chunk), 2):
        row = []
        for j in range(2):
            if i + j < len(chunk):
                aid, name, unlocked = chunk[i + j]
                prefix = "🏆" if unlocked else "🔒"
                text = f"{prefix} {name}"[:64]
                cb = f"ach_view:{aid}" if unlocked else f"ach_lock:{aid}"
                row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if row:
            rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t(lang, "ach_prev"), callback_data=f"ach_page_{page - 1}"))
    if start + PER_PAGE < total:
        nav.append(InlineKeyboardButton(text=t(lang, "ach_next"), callback_data=f"ach_page_{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="profile")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
