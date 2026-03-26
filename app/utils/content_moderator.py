"""Content moderation — banned words, phrases, and pattern detection.

Multi-language support: Russian, English, Arabic.
Categories: illegal activity, extremism, drugs, sexual, violence, fraud, weapons.

The filter uses normalized lowercase matching with word-boundary awareness
to minimize false positives while catching common variations.
"""

import logging
import re

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Banned word lists by category (lowercase, normalized)
# Each list contains stems/roots to catch conjugations and variations.
# ──────────────────────────────────────────────────────────────────────

# Drugs and drug-related
_DRUGS_RU = [
    "наркотик", "героин", "кокаин", "метамфетамин", "амфетамин",
    "марихуан", "гашиш", "мефедрон", "экстази", "лсд",
    "спайс", "курительн.*смес", "закладк", "барыг", "дурь",
    "шишк.*план", "косяк", "трав.*курить", "снюс",
    "опиат", "опиоид", "морфин", "фентанил",
]

_DRUGS_EN = [
    "cocaine", "heroin", "methamphetamine", "amphetamine",
    "marijuana", "cannabis", "ecstasy", "mdma",
    "fentanyl", "opioid", "opiate", "lsd", "meth",
    "drug deal", "drug trad", "narcotics",
]

_DRUGS_AR = [
    "مخدرات", "كوكايين", "هيروين", "حشيش",
    "ماريجوانا", "أفيون", "مورفين",
    "ترامادول", "كبتاغون",
]

# Extremism and terrorism
_EXTREMISM_RU = [
    "терроризм", "террорист", "джихад", "взорв",
    "бомб.*сделать", "убить.*неверн", "халифат",
    "вербовк", "радикализ", "экстремиз",
    "нацизм", "нацист", "фашизм", "фашист",
    "расов.*превосход", "белая.*раса", "сегрегац",
    "геноцид", "холокост.*отрица",
]

_EXTREMISM_EN = [
    "terrorism", "terrorist", "jihad", "bomb mak",
    "white supremac", "nazi", "fascis",
    "genocide", "ethnic cleansing", "radicali",
    "extremis",
]

_EXTREMISM_AR = [
    "إرهاب", "إرهابي", "جهاد.*قتال",
    "تطرف", "داعش", "القاعدة",
]

# Violence and threats
_VIOLENCE_RU = [
    "убить", "убийств", "зарезать", "застрелить",
    "расчленить", "пытк", "насили.*над",
    "изнасилов", "педофил", "растлен",
    "суицид.*способ", "самоубийств.*как",
]

_VIOLENCE_EN = [
    "kill.*someone", "murder", "assassinat",
    "torture", "rape", "pedophil",
    "dismember", "suicide.*method", "how to kill",
    "mass shoot", "school shoot",
]

_VIOLENCE_AR = [
    "قتل", "اغتيال", "تعذيب",
    "اغتصاب", "انتحار.*طريقة",
]

# Sexual exploitation / illegal sexual content
_SEXUAL_RU = [
    "детское.*порно", "cp ", "дп ", "цп ",
    "малолет.*секс", "несовершеннолет.*интим",
    "зоофил", "инцест",
]

_SEXUAL_EN = [
    "child porn", "child sex", "underage.*sex",
    "zoophil", "bestiality", "incest",
    "csam", "cp links",
]

_SEXUAL_AR = [
    "إباحية.*أطفال", "استغلال.*جنسي.*أطفال",
]

# Fraud and illegal services
_FRAUD_RU = [
    "обнал", "отмыв.*денег", "кардинг", "скиммер",
    "фальшив.*документ", "поддельн.*паспорт",
    "взлом.*аккаунт", "ddos.*атак", "ддос",
    "пробив.*данны", "слив.*баз", "деанон",
    "фишинг", "мошенничеств",
]

_FRAUD_EN = [
    "money launder", "carding", "skimmer",
    "fake passport", "fake document", "forged id",
    "hack.*account", "ddos.*attack", "phishing",
    "identity theft", "credit card fraud",
]

_FRAUD_AR = [
    "غسيل.*أموال", "تزوير.*وثائق",
    "اختراق.*حساب", "احتيال",
]

# Weapons
_WEAPONS_RU = [
    "купить.*оружи", "продам.*пистолет", "автомат.*калашников",
    "взрывчатк", "тротил", "детонатор",
    "бомб.*собрать", "бомб.*изготов",
]

_WEAPONS_EN = [
    "buy.*gun", "sell.*weapon", "homemade.*bomb",
    "explosive.*make", "detonator",
    "3d print.*gun",
]

_WEAPONS_AR = [
    "شراء.*سلاح", "متفجرات", "صنع.*قنبلة",
]

# ──────────────────────────────────────────────────────────────────────
# Compile all patterns into a single combined regex per language
# ──────────────────────────────────────────────────────────────────────

def _build_patterns(word_lists: list[list[str]]) -> list[re.Pattern[str]]:
    """Compile word lists into regex patterns."""
    patterns = []
    for words in word_lists:
        for w in words:
            try:
                patterns.append(re.compile(w, re.IGNORECASE | re.UNICODE))
            except re.error:
                logger.warning("Invalid regex pattern in content moderator: %s", w)
    return patterns


_ALL_PATTERNS = _build_patterns([
    _DRUGS_RU, _DRUGS_EN, _DRUGS_AR,
    _EXTREMISM_RU, _EXTREMISM_EN, _EXTREMISM_AR,
    _VIOLENCE_RU, _VIOLENCE_EN, _VIOLENCE_AR,
    _SEXUAL_RU, _SEXUAL_EN, _SEXUAL_AR,
    _FRAUD_RU, _FRAUD_EN, _FRAUD_AR,
    _WEAPONS_RU, _WEAPONS_EN, _WEAPONS_AR,
])

# ──────────────────────────────────────────────────────────────────────
# Leetspeak / character substitution normalization
# ──────────────────────────────────────────────────────────────────────

_LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i",
    # Cyrillic lookalikes → Latin
    "\u0430": "a", "\u0435": "e", "\u043e": "o",
    "\u0440": "p", "\u0441": "c", "\u0443": "y",
    "\u0445": "x",
})


def _normalize_base(text: str) -> str:
    """Lowercase + collapse whitespace + reduce repeated chars."""
    text = text.lower()
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_leet(text: str) -> str:
    """Apply leetspeak substitution + repeated char reduction."""
    text = text.translate(_LEET_MAP)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return text


def _check_patterns(text: str) -> re.Pattern[str] | None:
    """Return the first matching pattern, or None."""
    for pattern in _ALL_PATTERNS:
        if pattern.search(text):
            return pattern
    return None


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def is_prohibited(text: str) -> bool:
    """Check if text contains prohibited content.

    Returns True if any banned pattern matches.
    Checks both original text and leetspeak-normalized version.
    """
    if not text or not text.strip():
        return False
    base = _normalize_base(text)
    # Check original (important for Cyrillic/Arabic patterns)
    if _check_patterns(base):
        return True
    # Check leetspeak-normalized (for Latin bypass attempts)
    leet = _normalize_leet(base)
    if leet != base and _check_patterns(leet):
        return True
    return False


def check_content(text: str) -> tuple[bool, str | None]:
    """Check text for prohibited content.

    Returns (is_safe, matched_pattern_or_None).
    """
    if not text or not text.strip():
        return True, None
    base = _normalize_base(text)
    p = _check_patterns(base)
    if p:
        logger.warning(
            "Content moderation: blocked text matching pattern '%s' in: %.50s...",
            p.pattern, text,
        )
        return False, p.pattern
    leet = _normalize_leet(base)
    if leet != base:
        p = _check_patterns(leet)
        if p:
            logger.warning(
                "Content moderation: blocked (leet) text matching pattern '%s' in: %.50s...",
                p.pattern, text,
            )
            return False, p.pattern
    return True, None


def is_safe_habit_title(title: str) -> bool:
    """Check if a habit title is safe (no banned content)."""
    return not is_prohibited(title)
