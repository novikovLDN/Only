"""Bowling mini-game — dice 🎳, strike = +3 days Premium."""

from datetime import datetime, timedelta, timezone

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.db import get_session_maker
from app.services import user_service
from app.texts import t

router = Router(name="game")

COOLDOWN_DAYS = 3
STRIKE_VALUE = 6
REWARD_DAYS = 3


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _can_play(user) -> tuple[bool, str | None]:
    """Return (can_play, cooldown_message or None)."""
    if not user.last_game_at:
        return True, None
    until = user.last_game_at
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    next_at = until + timedelta(days=COOLDOWN_DAYS)
    now = _now()
    if now < next_at:
        delta = next_at - now
        days = delta.days
        hours = delta.seconds // 3600
        return False, t(
            user.language_code or "ru", "game_cooldown",
            days=days, hours=hours
        )
    return True, None


async def _run_game(bot: Bot, chat_id: int, tid: int) -> None:
    sm = get_session_maker()
    async with sm() as session:
        user = await user_service.get_by_telegram_id(session, tid)
        if not user:
            return
        lang = user.language_code if user.language_code in ("ru", "en", "ar") else "ru"
        can_play, cooldown_msg = _can_play(user)
        if not can_play:
            await bot.send_message(chat_id, cooldown_msg)
            return

        dice_msg = await bot.send_dice(chat_id=chat_id, emoji="🎳")
        value = dice_msg.dice.value if dice_msg.dice else 0

        now = _now()
        user.last_game_at = now

        if value == STRIKE_VALUE:
            user.game_wins = (user.game_wins or 0) + 1
            if user.premium_until:
                pu = user.premium_until
                if pu.tzinfo is None:
                    pu = pu.replace(tzinfo=timezone.utc)
                if pu > now:
                    user.premium_until = pu + timedelta(days=REWARD_DAYS)
                else:
                    user.premium_until = now + timedelta(days=REWARD_DAYS)
            else:
                user.premium_until = now + timedelta(days=REWARD_DAYS)
            await session.commit()
            await bot.send_message(chat_id, t(lang, "game_strike"))
        else:
            await session.commit()
            await bot.send_message(chat_id, t(lang, "game_no_strike"))


@router.message(F.text == "🎳")
@router.message(Command("game"))
async def game_play(message: Message) -> None:
    tid = message.from_user.id if message.from_user else 0
    chat_id = message.chat.id if message.chat else tid
    await _run_game(message.bot, chat_id, tid)


@router.callback_query(F.data == "game")
async def game_callback(cb: CallbackQuery) -> None:
    await cb.answer()
    tid = cb.from_user.id if cb.from_user else 0
    chat_id = cb.message.chat.id if cb.message else tid
    if cb.bot:
        await _run_game(cb.bot, chat_id, tid)
