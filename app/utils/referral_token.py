"""HMAC-based referral tokens — unpredictable referral links."""

import hashlib
import hmac

from app.config import settings


def generate_referral_code(user_id: int) -> str:
    """Generate HMAC-signed referral code for a user.

    Format: ref_{user_id}_{signature[:8]}
    If REFERRAL_SECRET is not set, falls back to plain ref_{user_id}.
    """
    if not settings.referral_secret:
        return f"ref_{user_id}"

    sig = hmac.new(
        settings.referral_secret.encode("utf-8"),
        str(user_id).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:8]
    return f"ref_{user_id}_{sig}"


def verify_referral_code(code: str) -> int | None:
    """Verify and extract user_id from referral code.

    Returns user_id if valid, None otherwise.
    Supports both signed (ref_{id}_{sig}) and legacy (ref_{id}) formats.
    """
    if not code.startswith("ref_"):
        return None

    parts = code[4:].split("_", 1)
    try:
        user_id = int(parts[0])
    except (ValueError, IndexError):
        return None

    # If no secret configured, accept any ref_ link (backwards compatible)
    if not settings.referral_secret:
        return user_id

    # If secret is set but code has no signature, reject
    if len(parts) < 2:
        return None

    expected_sig = hmac.new(
        settings.referral_secret.encode("utf-8"),
        str(user_id).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:8]

    if hmac.compare_digest(expected_sig, parts[1]):
        return user_id
    return None
