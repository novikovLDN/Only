"""Tests for crypto service — signature verification and webhook processing."""

import hashlib
import hmac
import base64
import json

import pytest

from app.services.crypto_service import _sign_body, verify_webhook_signature


TEST_API_KEY = "test_api_key_12345"


class TestSignBody:
    def test_signature_deterministic(self):
        body = {"amount": "1.00", "currency": "USD"}
        sig1 = _sign_body(body, TEST_API_KEY)
        sig2 = _sign_body(body, TEST_API_KEY)
        assert sig1 == sig2

    def test_different_bodies_different_sigs(self):
        body1 = {"amount": "1.00"}
        body2 = {"amount": "2.00"}
        sig1 = _sign_body(body1, TEST_API_KEY)
        sig2 = _sign_body(body2, TEST_API_KEY)
        assert sig1 != sig2

    def test_signature_format_hex(self):
        body = {"test": "value"}
        sig = _sign_body(body, TEST_API_KEY)
        assert len(sig) == 64  # SHA256 hex digest
        assert all(c in "0123456789abcdef" for c in sig)


class TestVerifyWebhookSignature:
    def _make_signed_data(self, data: dict) -> dict:
        """Create properly signed data dict."""
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        sig = hmac.new(
            TEST_API_KEY.encode("utf-8"),
            b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        data["sign"] = sig
        return data

    def test_valid_signature(self):
        data = {"uuid": "abc123", "status": "paid"}
        signed = self._make_signed_data(data.copy())
        assert verify_webhook_signature(signed, TEST_API_KEY) is True

    def test_invalid_signature(self):
        data = {"uuid": "abc123", "status": "paid", "sign": "invalid_signature"}
        assert verify_webhook_signature(data, TEST_API_KEY) is False

    def test_missing_signature(self):
        data = {"uuid": "abc123", "status": "paid"}
        assert verify_webhook_signature(data, TEST_API_KEY) is False

    def test_empty_api_key(self):
        data = {"uuid": "abc123", "sign": "something"}
        assert verify_webhook_signature(data, "") is False

    def test_tampered_data(self):
        data = {"uuid": "abc123", "amount": "10.00"}
        signed = self._make_signed_data(data.copy())
        signed["amount"] = "999.00"  # tamper after signing
        # Note: sign was already popped in verify, so reconstruct
        data2 = {"uuid": "abc123", "amount": "999.00"}
        data2["sign"] = signed.get("sign", "")
        # This should fail because data was modified
        result = verify_webhook_signature(data2, TEST_API_KEY)
        assert result is False
