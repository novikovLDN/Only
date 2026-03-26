"""Tests for streak recovery service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.streak_recovery_service import (
    FREE_RECOVERIES_PER_MONTH,
    PREMIUM_RECOVERIES_PER_MONTH,
    can_recover_streak,
    get_max_recoveries,
)


class TestGetMaxRecoveries:
    def test_free_user(self, sample_user):
        sample_user.premium_until = None
        assert get_max_recoveries(sample_user) == FREE_RECOVERIES_PER_MONTH

    def test_premium_user(self, premium_user):
        assert get_max_recoveries(premium_user) == PREMIUM_RECOVERIES_PER_MONTH


class TestCanRecoverStreak:
    def test_fresh_user_can_recover(self, sample_user):
        sample_user.streak_recoveries_used = 0
        sample_user.last_streak_recovery_at = None
        assert can_recover_streak(sample_user) is True

    def test_exhausted_free_user(self, sample_user):
        sample_user.premium_until = None
        sample_user.streak_recoveries_used = FREE_RECOVERIES_PER_MONTH
        sample_user.last_streak_recovery_at = datetime.now(timezone.utc)
        assert can_recover_streak(sample_user) is False

    def test_reset_after_30_days(self, sample_user):
        sample_user.streak_recoveries_used = FREE_RECOVERIES_PER_MONTH
        sample_user.last_streak_recovery_at = datetime.now(timezone.utc) - timedelta(days=31)
        assert can_recover_streak(sample_user) is True

    def test_premium_has_more_recoveries(self, premium_user):
        premium_user.streak_recoveries_used = FREE_RECOVERIES_PER_MONTH
        premium_user.last_streak_recovery_at = datetime.now(timezone.utc)
        # Premium users get more, so they should still be able to recover
        assert can_recover_streak(premium_user) is True
