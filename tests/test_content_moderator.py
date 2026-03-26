"""Tests for content moderation — banned words, leetspeak, multilingual."""

import pytest

from app.utils.content_moderator import (
    check_content,
    is_prohibited,
    is_safe_habit_title,
)


class TestIsProhibited:
    # ── Drugs ──
    def test_drugs_ru(self):
        assert is_prohibited("купить наркотики") is True

    def test_drugs_en(self):
        assert is_prohibited("cocaine dealer") is True

    def test_drugs_ar(self):
        assert is_prohibited("شراء مخدرات") is True

    # ── Extremism ──
    def test_extremism_ru(self):
        assert is_prohibited("терроризм хорошо") is True

    def test_extremism_en(self):
        assert is_prohibited("join terrorism group") is True

    # ── Violence ──
    def test_violence_ru(self):
        assert is_prohibited("хочу убить") is True

    def test_violence_en(self):
        assert is_prohibited("how to murder") is True

    # ── Sexual exploitation ──
    def test_sexual_en(self):
        assert is_prohibited("child porn links") is True

    # ── Fraud ──
    def test_fraud_ru(self):
        assert is_prohibited("обнал карт") is True

    def test_fraud_en(self):
        assert is_prohibited("money laundering scheme") is True

    # ── Weapons ──
    def test_weapons_ru(self):
        assert is_prohibited("купить оружие") is True

    def test_weapons_en(self):
        assert is_prohibited("buy a gun illegally") is True

    # ── Safe content ──
    def test_safe_habit_text(self):
        assert is_prohibited("Morning jog") is False

    def test_safe_ru(self):
        assert is_prohibited("Утренняя зарядка") is False

    def test_safe_ar(self):
        assert is_prohibited("قراءة الكتب") is False

    def test_empty_safe(self):
        assert is_prohibited("") is False

    def test_whitespace_safe(self):
        assert is_prohibited("   ") is False


class TestLeetspeakBypass:
    def test_leet_doesnt_bypass(self):
        # "c0c@ine" → normalized to "cocaine"
        assert is_prohibited("c0c@ine") is True

    def test_repeated_chars_normalized(self):
        # "coocaiine" → "cocaine" after repeat reduction + leet
        assert is_prohibited("c0caine") is True


class TestCheckContent:
    def test_safe_returns_true_none(self):
        safe, pattern = check_content("Morning meditation")
        assert safe is True
        assert pattern is None

    def test_prohibited_returns_false_and_pattern(self):
        safe, pattern = check_content("buy cocaine now")
        assert safe is False
        assert pattern is not None

    def test_empty_is_safe(self):
        safe, pattern = check_content("")
        assert safe is True


class TestIsSafeHabitTitle:
    def test_safe_title(self):
        assert is_safe_habit_title("Read 30 minutes") is True

    def test_unsafe_title(self):
        assert is_safe_habit_title("buy cocaine daily") is False

    def test_safe_russian_title(self):
        assert is_safe_habit_title("Пить воду каждый день") is True
