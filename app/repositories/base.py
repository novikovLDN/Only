"""
Base repository with common CRUD operations.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository with common operations."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, id: int) -> ModelT | None:
        """Get entity by primary key."""
        result = await self._session.execute(select(self._model).where(self._model.id == id))
        return result.scalar_one_or_none()

    async def add(self, entity: ModelT) -> ModelT:
        """Add entity to session."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete entity."""
        await self._session.delete(entity)
