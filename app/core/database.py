"""Database connection and session management."""

import logging
import subprocess
import sys
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

_engine = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _mask_url(url: str) -> str:
    """Mask credentials, show host."""
    if "@" in url:
        return url.split("@")[-1].split("?")[0]
    return "***"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_maker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def run_migrations() -> None:
    """Run Alembic migrations. Exit immediately on failure."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Migration failed: %s", result.stderr or result.stdout)
        raise RuntimeError(f"Alembic migration failed: {result.stderr or result.stdout}")


async def init_db() -> None:
    """Verify DB connection. Schema managed ONLY by Alembic (run migrations before app start)."""
    engine = get_engine()
    logger.info("DATABASE host: %s", _mask_url(settings.database_url))
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
