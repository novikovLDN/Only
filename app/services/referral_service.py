"""Referral service."""

from app.core.models import User
from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository

REFERRAL_BONUS_DAYS = 7


class ReferralService:
    def __init__(self, referral_repo: ReferralRepository, user_repo: UserRepository):
        self.referral_repo = referral_repo
        self.user_repo = user_repo

    async def apply_referral(self, invited_user: User, inviter_user_id: int) -> bool:
        if inviter_user_id == invited_user.id:
            return False
        exists = await self.referral_repo.exists(inviter_user_id, invited_user.id)
        if exists:
            return False
        await self.referral_repo.create(inviter_user_id, invited_user.id)
        inviter = await self.user_repo.get_by_id(inviter_user_id)
        if inviter:
            await self.user_repo.extend_subscription(inviter, REFERRAL_BONUS_DAYS)
        return True
