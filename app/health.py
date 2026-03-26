"""Health endpoint and webhooks for Railway."""

import logging

from fastapi import FastAPI

from app.api.webhooks.crypto import router as crypto_webhook_router

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(crypto_webhook_router)


@app.get("/health")
async def health() -> dict:
    """Extended health check — verifies DB connectivity and scheduler status."""
    status = {"status": "ok", "checks": {}}

    # Check database connectivity
    try:
        from app.database import get_session_maker
        sm = get_session_maker()
        async with sm() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {e}"
        status["status"] = "degraded"

    # Check scheduler
    try:
        from app.scheduler import get_scheduler
        sched = get_scheduler()
        if sched.running:
            status["checks"]["scheduler"] = "ok"
            status["checks"]["scheduler_jobs"] = len(sched.get_jobs())
        else:
            status["checks"]["scheduler"] = "not_running"
            status["status"] = "degraded"
    except Exception as e:
        status["checks"]["scheduler"] = f"error: {e}"

    return status
