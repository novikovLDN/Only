"""Tests for discount service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.services.discount_service import calculate_price_with_discount, is_discount_active


class TestIsDiscountActive:
    def test_no_user(self):
        assert is_discount_active(None) is False

    def test_no_discount_percent(self, sample_user):
        sample_user.discount_percent = 0
        assert is_discount_active(sample_user) is False

    def test_no_discount_until(self, sample_user):
        sample_user.discount_percent = 10
        sample_user.discount_until = None
        assert is_discount_active(sample_user) is False

    def test_expired_discount(self, sample_user):
        sample_user.discount_percent = 10
        sample_user.discount_until = datetime.now(timezone.utc) - timedelta(days=1)
        assert is_discount_active(sample_user) is False

    def test_active_discount(self, sample_user):
        sample_user.discount_percent = 10
        sample_user.discount_until = datetime.now(timezone.utc) + timedelta(days=7)
        assert is_discount_active(sample_user) is True

    def test_discount_without_tz(self, sample_user):
        """Test discount_until without timezone info (naive datetime)."""
        sample_user.discount_percent = 20
        sample_user.discount_until = datetime.utcnow() + timedelta(days=5)
        sample_user.discount_until = sample_user.discount_until.replace(tzinfo=None)
        # Should handle naive datetime
        result = is_discount_active(sample_user)
        assert isinstance(result, bool)


class TestCalculatePriceWithDiscount:
    def test_no_discount(self, sample_user):
        sample_user.discount_percent = 0
        final_kopecks, pct, original = calculate_price_with_discount(sample_user, 99.0)
        assert final_kopecks == 9900
        assert pct == 0
        assert original == 99.0

    def test_10_percent_discount(self, sample_user):
        sample_user.discount_percent = 10
        sample_user.discount_until = datetime.now(timezone.utc) + timedelta(days=7)
        final_kopecks, pct, original = calculate_price_with_discount(sample_user, 100.0)
        assert pct == 10
        assert final_kopecks == 9000  # 90 RUB * 100
        assert original == 100.0

    def test_50_percent_discount(self, sample_user):
        sample_user.discount_percent = 50
        sample_user.discount_until = datetime.now(timezone.utc) + timedelta(days=7)
        final_kopecks, pct, original = calculate_price_with_discount(sample_user, 200.0)
        assert pct == 50
        assert final_kopecks == 10000  # 100 RUB * 100

    def test_none_user(self):
        final_kopecks, pct, original = calculate_price_with_discount(None, 99.0)
        assert final_kopecks == 9900
        assert pct == 0

    def test_expired_discount_no_reduction(self, sample_user):
        sample_user.discount_percent = 30
        sample_user.discount_until = datetime.now(timezone.utc) - timedelta(days=1)
        final_kopecks, pct, original = calculate_price_with_discount(sample_user, 99.0)
        assert pct == 0  # discount expired
        assert final_kopecks == 9900

    def test_rounding_ceil(self, sample_user):
        """Verify math.ceil rounding to whole ruble."""
        sample_user.discount_percent = 33
        sample_user.discount_until = datetime.now(timezone.utc) + timedelta(days=7)
        final_kopecks, pct, original = calculate_price_with_discount(sample_user, 99.0)
        assert pct == 33
        # 99 * 67/100 = 66.33, ceil = 67 RUB = 6700 kopecks
        assert final_kopecks == 6700
