"""
Runtime state — schema drift, degraded mode.

Used by bootstrap, scheduler, middleware.
"""

# True = schema OK, full functionality
# False = schema drift detected, degraded mode (no scheduler, minimal user context)
_schema_ok: bool = True

# Circuit breaker: when habit_reminders hits schema error, stop re-running until restart
_scheduler_schema_tripped: bool = False


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
