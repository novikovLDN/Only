"""XP and level-up logic."""

import random

from aiogram import Bot

from app.core.levels import MAX_LEVEL, get_required_xp
from app.texts import t

LEVEL_PHRASES = {
    "ru": [
        "🔥 Ты растёшь!",
        "🚀 Новый уровень — новая версия тебя!",
        "💎 Так держать!",
        "🏆 Прогресс виден!",
        "⚡ Система работает!",
    ],
    "en": [
        "🔥 You're growing!",
        "🚀 New level — new version of you!",
        "💎 Keep going!",
        "🏆 Progress is visible!",
        "⚡ System upgrade!",
    ],
}


async def add_xp(user, session, bot: Bot) -> None:
    """Add 1 XP for completed habit. Level up and notify if threshold reached."""
    if user.level >= MAX_LEVEL:
        return

    user.xp = (user.xp or 0) + 1
    required = get_required_xp(user.level)

    if user.xp >= required:
        user.xp = 0
        user.level += 1
        if user.level > MAX_LEVEL:
            user.level = MAX_LEVEL
            user.xp = 0

        lang = (user.language_code or "ru")[:2].lower()
        lang = "en" if lang == "en" else "ru"
        phrases = LEVEL_PHRASES[lang]
        phrase = random.choice(phrases)
        level_text = t(lang, "level_up") + f" {user.level}!\n\n{phrase}"

        try:
            await bot.send_message(
                user.telegram_id,
                f"🎉 {level_text}",
            )
        except Exception:
            pass

    await session.flush()
