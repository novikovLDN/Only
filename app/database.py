"""Database connection and session — production-ready."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_engine():
    return _get_engine()


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    sm = get_session_maker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables if not exist. Idempotent — safe on every startup."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_indexes(engine)
    from app.db_seed import seed_achievements
    await seed_achievements()
    logger.info("Database schema ensured")


async def _ensure_indexes(engine) -> None:
    """Add indexes that may be missing (idempotent)."""
    from sqlalchemy import text
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_timezone ON users (timezone)",
    ]
    async with engine.begin() as conn:
        for sql in indexes:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning("Index creation skipped: %s", e)


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
