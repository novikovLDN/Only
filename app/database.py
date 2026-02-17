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
    await _migrate_crypto_columns(engine)
    await _migrate_discount_columns(engine)
    await _migrate_game_columns(engine)
    await _ensure_indexes(engine)
    from app.db_seed import seed_achievements
    await seed_achievements()
    logger.info("Database schema ensured")


async def _ensure_indexes(engine) -> None:
    """Add indexes that may be missing (idempotent)."""
    from sqlalchemy import text
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_timezone ON users (timezone)",
        "CREATE INDEX IF NOT EXISTS idx_users_discount_until ON users (discount_until)",
        "CREATE INDEX IF NOT EXISTS idx_users_last_game_at ON users (last_game_at)",
        "CREATE INDEX IF NOT EXISTS idx_payments_external_id ON payments (external_payment_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_crypto_network ON payments (crypto_network)",
    ]
    async with engine.begin() as conn:
        for sql in indexes:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning("Index creation skipped: %s", e)


async def _migrate_discount_columns(engine) -> None:
    """Add discount columns if missing (idempotent)."""
    from sqlalchemy import text
    user_cols = [
        ("discount_percent", "INTEGER NOT NULL DEFAULT 0"),
        ("discount_until", "TIMESTAMP WITH TIME ZONE"),
        ("discount_given_by", "BIGINT"),
        ("discount_created_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    payment_cols = [
        ("original_amount", "NUMERIC(10,2)"),
        ("discount_percent_applied", "INTEGER DEFAULT 0"),
    ]
    async with engine.begin() as conn:
        for name, typ in user_cols:
            try:
                await conn.execute(text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {name} {typ}"
                ))
            except Exception as e:
                logger.warning("Migration users.%s skipped: %s", name, e)
        for name, typ in payment_cols:
            try:
                await conn.execute(text(
                    f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {name} {typ}"
                ))
            except Exception as e:
                logger.warning("Migration payments.%s skipped: %s", name, e)


async def _migrate_game_columns(engine) -> None:
    """Add game columns if missing (idempotent)."""
    from sqlalchemy import text
    cols = [
        ("last_game_at", "TIMESTAMP WITH TIME ZONE"),
        ("game_wins", "INTEGER NOT NULL DEFAULT 0"),
    ]
    async with engine.begin() as conn:
        for name, typ in cols:
            try:
                await conn.execute(text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {name} {typ}"
                ))
            except Exception as e:
                logger.warning("Migration users.%s skipped: %s", name, e)


async def _migrate_crypto_columns(engine) -> None:
    """Add crypto columns if missing (idempotent)."""
    from sqlalchemy import text
    cols = [
        ("crypto_network", "VARCHAR(50)"),
        ("crypto_currency", "VARCHAR(20)"),
        ("crypto_address", "VARCHAR(255)"),
        ("expires_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    async with engine.begin() as conn:
        for name, typ in cols:
            try:
                await conn.execute(text(
                    f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {name} {typ}"
                ))
            except Exception as e:
                logger.warning("Migration column %s skipped: %s", name, e)


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
