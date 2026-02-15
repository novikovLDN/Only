"""Referral service — atomic, transaction-safe."""

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.repositories.referral_repo import ReferralRepository
from app.repositories.user_repo import UserRepository

REFERRAL_BONUS_DAYS = 7
logger = logging.getLogger(__name__)


@dataclass
class ReferralResult:
    success: bool
    new_user: User | None
    inviter_telegram_id: int | None
    inviter_lang: str | None


class ReferralService:
    def __init__(self, referral_repo: ReferralRepository, user_repo: UserRepository):
        self.referral_repo = referral_repo
        self.user_repo = user_repo

    async def process_referral(
        self,
        session: AsyncSession,
        inviter_tg_id: int,
        new_user_tg_id: int,
        username: str | None = None,
        first_name: str = "",
    ) -> ReferralResult:
        existing = await self.user_repo.get_by_telegram_id(new_user_tg_id)
        if existing:
            logger.warning("Referral ignored reason=existing_user inviter=%s invited=%s", inviter_tg_id, new_user_tg_id)
            return ReferralResult(False, None, None, None)

        if inviter_tg_id == new_user_tg_id:
            logger.warning("Referral ignored reason=self_referral inviter=%s", inviter_tg_id)
            return ReferralResult(False, None, None, None)

        inviter = await self.user_repo.get_by_telegram_id(inviter_tg_id)
        if not inviter:
            logger.warning("Referral ignored reason=inviter_not_found inviter=%s invited=%s", inviter_tg_id, new_user_tg_id)
            return ReferralResult(False, None, None, None)

        new_user = await self.user_repo.create(
            telegram_id=new_user_tg_id,
            username=username,
            first_name=first_name,
            language=None,
            invited_by_id=inviter.id,
        )

        try:
            await self.referral_repo.create(inviter.id, new_user.id)
        except Exception as e:
            logger.warning("Referral ignored reason=db_constraint invited=%s err=%s", new_user_tg_id, e)
            raise

        inviter_locked = await self.user_repo.get_by_id_for_update(inviter.id)
        if inviter_locked:
            await self.user_repo.extend_subscription(inviter_locked, REFERRAL_BONUS_DAYS)

        logger.info("Referral success inviter=%s invited=%s", inviter_tg_id, new_user_tg_id)
        return ReferralResult(
            True,
            new_user,
            inviter.telegram_id,
            inviter.language or "en",
        )
