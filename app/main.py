"""
Entry point — bot startup, graceful shutdown.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from app.config import settings
from app.fsm.storage import storage
from app.handlers import start, habits, admin
from app.middlewares import ThrottlingMiddleware, UserContextMiddleware
from app.models.base import init_db, close_db
from app.monitoring.health import full_health_check
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Health server
_health_app: web.Application | None = None
_health_runner: web.AppRunner | None = None


async def health_handler(request: web.Request) -> web.Response:
    """GET /health for Railway."""
    status = await full_health_check()
    return web.json_response(
        {"ok": status.ok, "details": status.details},
        status=200 if status.ok else 503,
    )


async def on_startup(bot: Bot) -> None:
    """Startup: init DB, setup scheduler, health server."""
    global _health_app, _health_runner
    logger.info("Starting bot...")
    await init_db()
    setup_scheduler(bot)
    # Health server for Railway
    _health_app = web.Application()
    _health_app.router.add_get("/health", health_handler)
    _health_runner = web.AppRunner(_health_app)
    await _health_runner.setup()
    site = web.TCPSite(_health_runner, "0.0.0.0", settings.health_check_port)
    await site.start()
    logger.info("Bot started.")


async def on_shutdown(bot: Bot) -> None:
    """Graceful shutdown."""
    global _health_runner
    logger.info("Shutting down...")
    if _health_runner:
        await _health_runner.cleanup()
    shutdown_scheduler()
    await close_db()
    logger.info("Shutdown complete.")


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
