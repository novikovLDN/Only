"""Bot entrypoint — pure long-polling with graceful shutdown."""

import asyncio
import logging
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import settings
from app.database import close_db, init_db
from app.logger import setup_logging
from app.middlewares.rate_limit import RateLimitMiddleware
from app.scheduler import setup_scheduler, shutdown_scheduler

from app.handlers import (
    admin,
    commands,
    complete_all,
    export,
    game,
    habits_create,
    habits_edit,
    loyalty,
    main_menu,
    notifications,
    premium,
    profile,
    settings as settings_handler,
    snooze,
    start,
)

logger = logging.getLogger(__name__)

_shutdown_event = asyncio.Event()


def _create_bot_and_dp() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register rate limiting middleware first
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())

    dp.include_router(admin.router)
    dp.include_router(commands.router)
    dp.include_router(complete_all.router)
    dp.include_router(export.router)
    dp.include_router(habits_create.router)
    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(habits_edit.router)
    dp.include_router(profile.router)
    dp.include_router(game.router)
    dp.include_router(premium.router)
    dp.include_router(loyalty.router)
    dp.include_router(settings_handler.router)
    dp.include_router(snooze.router)
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
        BotCommand(command="start", description="Restart"),
        BotCommand(command="add", description="Add habit"),
        BotCommand(command="edit", description="Edit habits"),
        BotCommand(command="profile", description="My profile"),
        BotCommand(command="premium", description="Buy Premium"),
        BotCommand(command="game", description="Game"),
        BotCommand(command="referral", description="Loyalty program"),
        BotCommand(command="settings", description="Settings"),
        BotCommand(command="export", description="Export my data"),
    ])

    logging.getLogger("aiogram").setLevel(logging.DEBUG)
    await bot.delete_webhook(drop_pending_updates=True)

    # Graceful shutdown via signals
    loop = asyncio.get_running_loop()

    def _signal_handler():
        logger.info("Shutdown signal received")
        _shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    try:
        polling_task = asyncio.create_task(dp.start_polling(bot))
        await _shutdown_event.wait()
        logger.info("Initiating graceful shutdown...")
        dp.shutdown()
    except Exception:
        pass
    finally:
        shutdown_scheduler()
        await close_db()
        logger.info("Bot stopped gracefully")


if __name__ == "__main__":
    asyncio.run(main())
