"""
Job execution logging — execution, errors, skips.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def job_execution_log(job_id: str) -> AsyncGenerator[None, None]:
    """
    Context manager: log start, duration, success/error.
    """
    start = time.monotonic()
    logger.info("Job started: %s", job_id)
    try:
        yield
        elapsed = time.monotonic() - start
        logger.info("Job completed: %s (%.2fs)", job_id, elapsed)
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.exception("Job failed: %s (%.2fs): %s", job_id, elapsed, e)
        raise


def log_job_skip(job_id: str, reason: str, **kwargs: str | int) -> None:
    """Log when job skips an item (e.g. user blocked, already notified)."""
    logger.info("Job skip [%s]: %s %s", job_id, reason, kwargs)
