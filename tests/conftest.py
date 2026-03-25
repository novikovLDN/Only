"""Test fixtures for habit bot tests."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment before importing app modules
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("ADMIN_ID", "12345")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create a test database engine."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """Create a test database session."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def sample_user():
    """Create a sample User object for testing."""
    from app.models import User
    return User(
        id=1,
        telegram_id=123456789,
        first_name="Test",
        username="testuser",
        language_code="en",
        timezone="Europe/Moscow",
        xp=0,
        level=1,
        premium_until=None,
        premium_reward_days=0,
        discount_percent=0,
        game_wins=0,
        trial_used=False,
        streak_recoveries_used=0,
    )


@pytest.fixture
def premium_user(sample_user):
    """Create a sample premium User."""
    sample_user.premium_until = datetime.now(timezone.utc) + timedelta(days=30)
    return sample_user
