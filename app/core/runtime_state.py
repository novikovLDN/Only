"""
Runtime state — schema drift, degraded mode, bot lock.

Used by bootstrap, scheduler, middleware.
"""

# True = schema OK, full functionality
# False = schema drift detected, degraded mode (no scheduler, minimal user context)
_schema_ok: bool = True

# Circuit breaker: when habit_reminders hits schema error, stop re-running until restart
_scheduler_schema_tripped: bool = False

# Context manager holding PostgreSQL advisory lock (released on shutdown)
_lock_ctx: object = None


def set_schema_ok(ok: bool) -> None:
    global _schema_ok
    _schema_ok = ok


def is_schema_ok() -> bool:
    return _schema_ok


def trip_scheduler_circuit() -> None:
    """Disable scheduler jobs until restart."""
    global _scheduler_schema_tripped
    _scheduler_schema_tripped = True


def is_scheduler_circuit_tripped() -> bool:
    return _scheduler_schema_tripped


def set_bot_lock_ctx(ctx) -> None:
    global _lock_ctx
    _lock_ctx = ctx


def get_bot_lock_ctx():
    return _lock_ctx


async def release_bot_lock() -> None:
    """Release PostgreSQL advisory lock on shutdown."""
    global _lock_ctx
    if _lock_ctx is not None:
        try:
            await _lock_ctx.__aexit__(None, None, None)
        except Exception:
            pass
        _lock_ctx = None
