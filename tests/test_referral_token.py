"""Tests for HMAC-based referral tokens."""

import os
import pytest


class TestReferralToken:
    def test_generate_without_secret(self):
        os.environ.pop("REFERRAL_SECRET", None)
        # Need to reimport to pick up new settings
        from app.utils.referral_token import generate_referral_code, verify_referral_code
        # Without secret, falls back to plain format
        code = generate_referral_code(12345)
        assert code.startswith("ref_12345")

    def test_verify_legacy_format(self):
        """Legacy ref_ links should still work without secret."""
        os.environ.pop("REFERRAL_SECRET", None)
        from app.utils.referral_token import verify_referral_code
        result = verify_referral_code("ref_12345")
        assert result == 12345

    def test_verify_invalid_format(self):
        from app.utils.referral_token import verify_referral_code
        assert verify_referral_code("invalid") is None
        assert verify_referral_code("ref_") is None
        assert verify_referral_code("ref_abc") is None
        assert verify_referral_code("") is None

    def test_verify_valid_id(self):
        from app.utils.referral_token import verify_referral_code
        result = verify_referral_code("ref_999")
        assert result == 999


class TestTexts:
    def test_normalize_lang(self):
        from app.texts import _normalize_lang
        assert _normalize_lang("ru") == "ru"
        assert _normalize_lang("en") == "en"
        assert _normalize_lang("ar") == "ar"
        assert _normalize_lang("de") == "ru"
        assert _normalize_lang(None) == "ru"
        assert _normalize_lang("") == "ru"

    def test_t_function_returns_string(self):
        from app.texts import t
        result = t("en", "main_greeting", name="Test")
        assert isinstance(result, str)
        assert "Test" in result

    def test_t_function_missing_key(self):
        from app.texts import t
        result = t("en", "nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_t_arabic_rtl_marker(self):
        from app.texts import t
        result = t("ar", "btn_back")
        assert result.startswith("\u200F")
