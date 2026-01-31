"""
Retry with exponential backoff for transient failures.
"""

import asyncio
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Retry async func with exponential backoff.
    base_delay * 2^attempt, capped at max_delay.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except retry_on as e:
            last_exc = e
            if attempt == max_attempts - 1:
                raise
            delay = min(base_delay * (2**attempt), max_delay)
            logger.warning("Retry %d/%d after %.1fs: %s", attempt + 1, max_attempts, delay, e)
            await asyncio.sleep(delay)
    raise last_exc or RuntimeError("Retry failed")
