"""
HTTP Health Server for Railway.

Railway expects an HTTP endpoint to verify the deployment is live.
Since the bot uses long-polling (no built-in HTTP), we run a minimal aiohttp
server in the same event loop as the bot.

Critical: must listen on PORT (Railway injects this) for healthcheck to succeed.
"""

import logging
from typing import Callable, Awaitable

from aiohttp import web

from app.monitoring.health import full_health_check

logger = logging.getLogger(__name__)

# Type for async health check (injected to avoid circular imports / pass bot)
HealthCheckFunc = Callable[[], Awaitable[object]]


async def create_deep_health_handler(
    health_check: HealthCheckFunc | None = None,
) -> web.RequestHandler:
    """Create GET /health/deep handler — detailed diagnostics."""

    async def handler(request: web.Request) -> web.Response:
        try:
            check = health_check or full_health_check
            status = await check()
            ok = getattr(status, "ok", False)
            details = getattr(status, "details", {})
            from app.core.runtime_state import is_schema_ok, is_scheduler_circuit_tripped
            details["schema_ok"] = is_schema_ok()
            details["scheduler_circuit_tripped"] = is_scheduler_circuit_tripped()
            return web.json_response(
                {"ok": ok, "details": details, "deep": True},
                status=200 if ok else 503,
            )
        except Exception as e:
            return web.json_response(
                {"ok": False, "error": str(e), "details": {}, "deep": True},
                status=503,
            )

    return handler


async def create_health_handler(
    health_check: HealthCheckFunc | None = None,
) -> web.RequestHandler:
    """
    Create GET /health handler.

    Args:
        health_check: Optional override. Default: full_health_check from health module.
    """

    async def handler(request: web.Request) -> web.Response:
        try:
            check = health_check or full_health_check
            status = await check()
            ok = getattr(status, "ok", False)
            details = getattr(status, "details", {})
            status_code = 200 if ok else 503
            if not ok:
                logger.warning("Healthcheck returned 503: %s", details)
            return web.json_response(
                {"ok": ok, "details": details},
                status=status_code,
            )
        except Exception as e:
            logger.exception("Healthcheck failed: %s", e)
            return web.json_response(
                {"ok": False, "error": str(e), "details": {}},
                status=503,
            )

    return handler


async def start_health_server(
    port: int,
    health_check: HealthCheckFunc | None = None,
) -> web.AppRunner:
    """
    Create and start health server. Returns AppRunner for cleanup on shutdown.

    Non-blocking: runs in the same event loop as the caller.
    Railway will hit GET /health on this port until it receives 200 OK.

    Args:
        port: Port to bind (use settings.http_port for Railway PORT).
        health_check: Optional custom check. Default uses full_health_check.
    """
    app = web.Application()
    handler = await create_health_handler(health_check=health_check)
    app.router.add_get("/health", handler)
    deep_handler = await create_deep_health_handler(health_check=health_check)
    app.router.add_get("/health/deep", deep_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("Health server listening on 0.0.0.0:%d (GET /health)", port)
    return runner
