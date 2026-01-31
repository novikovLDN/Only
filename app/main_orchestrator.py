"""
Entrypoint-оркестратор.

Собирает Bot, Dispatcher, подключает роутеры и middlewares.
Управляет lifecycle: startup (health server, db, scheduler) → polling → shutdown.

Бизнес-логика не выполняется здесь — только сборка и запуск.

Railway: ensure single instance (scale=1). Multiple instances cause
TelegramConflictError (only one getUpdates allowed per bot token).
"""

import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramConflictError
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Core
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.health import full_health_check
from app.core.health_server import start_health_server
from app.core.scheduler import setup_scheduler, shutdown_scheduler

# Infrastructure
from app.models.base import init_db, close_db

# Bot
from app.fsm.storage import storage
from app.bot.router import router as bot_router
from app.bot.middlewares import ThrottlingMiddleware, UserContextMiddleware
from app.middlewares.fsm_middleware import FSMTimeoutMiddleware

logger = logging.getLogger(__name__)

# Health server runner — для cleanup при shutdown
_health_runner = None


async def on_startup(bot: Bot) -> None:
    """
    Startup: health server → db → scheduler.

    Health server первым — Railway может проверять /health до готовности
    остальных компонентов (получит 503, затем 200).
    """
    global _health_runner

    logger.info("Starting...")

    # 1. Health server (Railway)
    port = settings.http_port
    _health_runner = await start_health_server(
        port=port,
        health_check=lambda: full_health_check(bot),
    )
    logger.info("Health server on port %d", port)

    # 2. Database
    await init_db()
    logger.info("Database ready")

    # 3. Scheduler
    setup_scheduler(bot)
    logger.info("Scheduler started")

    logger.info("Startup complete")


async def on_shutdown(bot: Bot) -> None:
    """Graceful shutdown."""
    global _health_runner

    logger.info("Shutting down...")

    if _health_runner:
        await _health_runner.cleanup()
        _health_runner = None
    await shutdown_scheduler()
    await close_db()

    logger.info("Shutdown complete")


def main() -> None:
    """Orchestrate and run."""
    setup_logging()

    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(FSMTimeoutMiddleware())
    dp.callback_query.middleware(FSMTimeoutMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())

    # Routers
    dp.include_router(bot_router)

    # Lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Run polling. TelegramConflictError = another instance polling same bot.
    try:
        dp.run_polling(bot)
    except TelegramConflictError as e:
        logger.critical(
            "TelegramConflictError: another instance is polling this bot. "
            "Railway: set scale=1. Error: %s",
            e,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
