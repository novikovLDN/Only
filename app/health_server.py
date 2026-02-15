"""Minimal health server for Railway."""

import asyncio
import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def start_health_server(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health server on :%d", port)
    return runner


async def on_startup(bot, bot_ref) -> None:
    from app.config import settings
    from app.core.database import init_db

    await init_db()
    port = settings.http_port
    runner = await start_health_server(port)
    bot_ref["health_runner"] = runner
    from app.scheduler import setup_scheduler
    setup_scheduler(bot)
    logger.info("Bot started")


async def on_shutdown(bot, bot_ref) -> None:
    from app.scheduler import shutdown_scheduler
    from app.core.database import close_db

    runner = bot_ref.get("health_runner")
    if runner:
        await runner.cleanup()
    shutdown_scheduler()
    await close_db()
    logger.info("Bot stopped")
