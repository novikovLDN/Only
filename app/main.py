"""Bot entrypoint — pure long-polling."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import settings
from app.database import close_db, init_db
from app.logger import setup_logging
from app.scheduler import setup_scheduler, shutdown_scheduler

from app.handlers import (
    admin,
    commands,
    game,
    habits_create,
    habits_edit,
    loyalty,
    main_menu,
    notifications,
    premium,
    profile,
    settings as settings_handler,
    start,
)

logger = logging.getLogger(__name__)


def _create_bot_and_dp() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(commands.router)
    dp.include_router(habits_create.router)
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(habits_edit.router)
    dp.include_router(profile.router)
    dp.include_router(game.router)
    dp.include_router(premium.router)
    dp.include_router(loyalty.router)
    dp.include_router(settings_handler.router)
    dp.include_router(notifications.router)

    return bot, dp


async def main() -> None:
    setup_logging()
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)

    _url = settings.database_url
    _safe = _url.split("@")[-1] if "@" in _url else "***"
    logger.info("DATABASE_URL (host): %s", _safe)

    await init_db()
    bot, dp = _create_bot_and_dp()
    setup_scheduler(bot)

    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Перезапуск"),
        BotCommand(command="add", description="➕ Добавить привычку"),
        BotCommand(command="edit", description="✏️ Редактировать привычки"),
        BotCommand(command="profile", description="👤 Мой профиль"),
        BotCommand(command="premium", description="💎 Купить Premium"),
        BotCommand(command="game", description="🎳 Игра"),
        BotCommand(command="referral", description="🌎 Программа лояльности"),
        BotCommand(command="settings", description="⚙️ Настройки"),
    ])

    logging.getLogger("aiogram").setLevel(logging.DEBUG)
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        shutdown_scheduler()
        await close_db()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
