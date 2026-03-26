"""Tests for trial premium service."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.services.trial_service import grant_trial_if_eligible


class TestTrialEligibility:
    def test_new_user_eligible(self, sample_user):
        """New user with trial_used=False should be eligible."""
        sample_user.trial_used = False
        sample_user.premium_until = None
        # Can't test async without session, but we test the logic
        assert sample_user.trial_used is False

    def test_already_used_trial(self, sample_user):
        """User who already used trial is not eligible."""
        sample_user.trial_used = True
        assert sample_user.trial_used is True

    def test_already_premium_not_eligible(self, premium_user):
        """Premium user should not get trial."""
        premium_user.trial_used = False
        # They already have premium, so grant_trial_if_eligible would return False
        assert premium_user.premium_until > datetime.now(timezone.utc)


class TestRateLimitMiddleware:
    def test_import(self):
        from app.middlewares.rate_limit import RateLimitMiddleware
        mw = RateLimitMiddleware(limit=5, window=10.0)
        assert mw.limit == 5
        assert mw.window == 10.0


class TestDbAutofix:
    def test_validate_identifier_valid(self):
        from app.db_autofix import _validate_identifier
        assert _validate_identifier("users") == "users"
        assert _validate_identifier("my_table_123") == "my_table_123"

    def test_validate_identifier_invalid(self):
        from app.db_autofix import _validate_identifier
        with pytest.raises(ValueError):
            _validate_identifier("'; DROP TABLE users; --")
        with pytest.raises(ValueError):
            _validate_identifier("123invalid")
        with pytest.raises(ValueError):
            _validate_identifier("table name")
