"""User service."""

from app.core.models import User
from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        language: str | None = None,
        invited_by_id: int | None = None,
    ) -> tuple[User, bool]:
        return await self.repo.get_or_create(
            telegram_id, username, first_name, language, invited_by_id
        )

    async def update_language(self, user: User, language: str) -> None:
        await self.repo.update_language(user, language)

    async def extend_subscription(self, user: User, days: int) -> None:
        await self.repo.extend_subscription(user, days)

    async def count_referrals(self, user_id: int) -> int:
        return await self.repo.count_referrals(user_id)
