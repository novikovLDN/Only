"""
Health checks — db, scheduler, bot.

Используется health_server для Railway.
"""

# Re-export from existing monitoring
from app.monitoring.health import (
    HealthStatus,
    full_health_check,
    check_db,
    check_scheduler,
    check_bot,
)
