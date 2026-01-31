"""
Health HTTP server (aiohttp).

Railway expects GET /health on $PORT.
Запускается в том же event loop, что и aiogram.
"""

# Re-export
from app.monitoring.health_server import start_health_server
