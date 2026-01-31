"""
Bot instance reference for error handlers and alerts.

Set by main orchestrator before polling. Avoids circular imports.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

_bot: "Bot | None" = None


def set_bot(bot: "Bot") -> None:
    global _bot
    _bot = bot


def get_bot() -> "Bot | None":
    return _bot
