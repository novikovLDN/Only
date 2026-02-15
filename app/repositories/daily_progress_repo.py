"""Daily progress repository."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.models import DailyProgress


class DailyProgressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, user_id: int, d: date, success: bool) -> None:
        stmt = insert(DailyProgress).values(user_id=user_id, date=d, success=success)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "date"],
            set_={"success": success},
        )
        await self.session.execute(stmt)
        await self.session.flush()
