"""Tests for input sanitizer — Unicode cleanup, size limits, Zalgo, emoji bomb."""

import pytest

from app.utils.input_sanitizer import (
    MAX_HABIT_TITLE_LENGTH,
    MAX_MESSAGE_LENGTH,
    is_emoji_bomb,
    normalize_unicode,
    sanitize_habit_title,
    sanitize_text,
    sanitize_username,
    strip_invisible,
    strip_zalgo,
)


class TestStripInvisible:
    def test_removes_zero_width_space(self):
        assert strip_invisible("hello\u200Bworld") == "helloworld"

    def test_removes_bidi_overrides(self):
        assert strip_invisible("abc\u202Edef") == "abcdef"

    def test_removes_bom(self):
        assert strip_invisible("\uFEFFhello") == "hello"

    def test_preserves_normal_text(self):
        assert strip_invisible("Hello World 123!") == "Hello World 123!"

    def test_removes_multiple_invisible(self):
        text = "\u200B\u200C\u200Dhello\u2060\uFEFF"
        assert strip_invisible(text) == "hello"


class TestNormalizeUnicode:
    def test_nfc_normalization(self):
        # e + combining acute = é in NFC
        result = normalize_unicode("e\u0301")
        assert result == "\u00e9"

    def test_strips_invisible_after_nfc(self):
        result = normalize_unicode("\u200Bhello\u200B")
        assert result == "hello"


class TestStripZalgo:
    def test_removes_excessive_combining(self):
        zalgo = "h\u0300\u0301\u0302\u0303ello"
        result = strip_zalgo(zalgo)
        assert result == "hello"

    def test_preserves_normal_diacritics(self):
        # Single combining mark is fine (< 3 threshold)
        assert strip_zalgo("e\u0301") == "e\u0301"


class TestIsEmojiBomb:
    def test_normal_text_not_bomb(self):
        assert is_emoji_bomb("Hello world") is False

    def test_empty_not_bomb(self):
        assert is_emoji_bomb("") is False

    def test_mostly_emoji_is_bomb(self):
        # 20 emoji characters > 70% of total
        text = "\U0001F600" * 20 + "ab"
        assert is_emoji_bomb(text) is True

    def test_short_emoji_not_bomb(self):
        # Short text (<=10 chars) is not a bomb even if all emoji
        assert is_emoji_bomb("\U0001F600\U0001F601") is False


class TestSanitizeText:
    def test_normal_text(self):
        assert sanitize_text("Hello World") == "Hello World"

    def test_empty_returns_none(self):
        assert sanitize_text("") is None
        assert sanitize_text(None) is None

    def test_too_long_returns_none(self):
        text = "a" * (MAX_MESSAGE_LENGTH + 1)
        assert sanitize_text(text) is None

    def test_within_limit(self):
        text = "a" * MAX_MESSAGE_LENGTH
        assert sanitize_text(text) is not None

    def test_collapses_whitespace(self):
        assert sanitize_text("hello   world") == "hello world"

    def test_strips_invisible_chars(self):
        result = sanitize_text("hello\u200Bworld")
        assert result == "helloworld"

    def test_only_whitespace_returns_none(self):
        assert sanitize_text("   \u200B   ") is None


class TestSanitizeHabitTitle:
    def test_normal_title(self):
        assert sanitize_habit_title("Morning jog") == "Morning jog"

    def test_too_long_returns_none(self):
        title = "x" * (MAX_HABIT_TITLE_LENGTH + 1)
        assert sanitize_habit_title(title) is None

    def test_empty_returns_none(self):
        assert sanitize_habit_title("") is None


class TestSanitizeUsername:
    def test_normal_name(self):
        assert sanitize_username("Alice") == "Alice"

    def test_empty_returns_user(self):
        assert sanitize_username("") == "User"

    def test_invisible_only_returns_user(self):
        assert sanitize_username("\u200B\u200C") == "User"
