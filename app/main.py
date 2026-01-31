"""
Entry point — bot startup, graceful shutdown.

Railway: expects HTTP GET /health on $PORT. Health server runs in the same
event loop as aiogram polling. See docs/HEALTHCHECK_ARCHITECTURE.md.
"""

import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.fsm.storage import storage
from app.handlers import start, habits, admin
from app.middlewares import ThrottlingMiddleware, UserContextMiddleware
from app.models.base import init_db, close_db
from app.monitoring.health import full_health_check
from app.monitoring.health_server import start_health_server
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Health server runner for cleanup on shutdown
_health_runner = None


async def on_startup(bot: Bot) -> None:
    """
    Startup: health server first (Railway), then DB, then scheduler.

    Order matters: health server must bind to PORT before Railway's first check.
    Returns 503 until all components are ready, then 200.
    """
    global _health_runner

    logger.info("Starting bot...")

    # 1. Health server — FIRST so Railway can reach us immediately.
    #    Listens on $PORT (Railway) or HEALTH_CHECK_PORT (local).
    #    Returns 503 until steps 2–3 complete.
    port = settings.http_port
    _health_runner = await start_health_server(
        port=port,
        health_check=lambda: full_health_check(bot),
    )
    logger.info("Health server bound to port %d", port)

    # 2. Database
    await init_db()
    logger.info("Database initialized")

    # 3. Scheduler
    setup_scheduler(bot)
    logger.info("Scheduler started")

    logger.info("Bot startup complete — health check will return 200")


async def on_shutdown(bot: Bot) -> None:
    """Graceful shutdown: health server, scheduler, DB."""
    global _health_runner

    logger.info("Shutting down...")

    if _health_runner:
        await _health_runner.cleanup()
        _health_runner = None
        logger.info("Health server stopped")

    await shutdown_scheduler()
    await close_db()
    logger.info("Shutdown complete")


def main() -> None:
    """Run bot."""
    if not settings.bot_token:
        logger.error("BOT_TOKEN not set")
        sys.exit(1)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(habits.router)
    dp.include_router(admin.router)

    # Lifecycle
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Run
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
