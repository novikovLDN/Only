"""Tests for user service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.user_service import (
    ALLOWED_TIMEZONES,
    _validate_iana_timezone,
    is_premium,
)


class TestIsPremium:
    def test_no_premium(self, sample_user):
        sample_user.premium_until = None
        assert is_premium(sample_user) is False

    def test_expired_premium(self, sample_user):
        sample_user.premium_until = datetime.now(timezone.utc) - timedelta(days=1)
        assert is_premium(sample_user) is False

    def test_active_premium(self, sample_user):
        sample_user.premium_until = datetime.now(timezone.utc) + timedelta(days=30)
        assert is_premium(sample_user) is True

    def test_naive_datetime_premium(self, sample_user):
        """Premium with naive datetime (no tzinfo)."""
        sample_user.premium_until = datetime.utcnow() + timedelta(days=30)
        sample_user.premium_until = sample_user.premium_until.replace(tzinfo=None)
        # Should handle naive datetime by treating as UTC
        result = is_premium(sample_user)
        assert result is True

    def test_just_expired(self, sample_user):
        """Premium that just expired (1 second ago)."""
        sample_user.premium_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert is_premium(sample_user) is False


class TestValidateTimezone:
    def test_valid_timezone(self):
        assert _validate_iana_timezone("Europe/Moscow") == "Europe/Moscow"
        assert _validate_iana_timezone("America/New_York") == "America/New_York"
        assert _validate_iana_timezone("Asia/Dubai") == "Asia/Dubai"

    def test_expanded_timezones(self):
        """Test newly added expanded timezones."""
        assert _validate_iana_timezone("Europe/Berlin") == "Europe/Berlin"
        assert _validate_iana_timezone("Asia/Tokyo") == "Asia/Tokyo"
        assert _validate_iana_timezone("Australia/Sydney") == "Australia/Sydney"
        assert _validate_iana_timezone("America/Los_Angeles") == "America/Los_Angeles"

    def test_invalid_timezone(self):
        assert _validate_iana_timezone("Invalid/Zone") == "Europe/Moscow"
        assert _validate_iana_timezone("") == "Europe/Moscow"
        assert _validate_iana_timezone(None) == "Europe/Moscow"

    def test_timezone_count(self):
        """Ensure we have 30+ timezones now."""
        assert len(ALLOWED_TIMEZONES) >= 30

    def test_utc_allowed(self):
        assert _validate_iana_timezone("UTC") == "UTC"
