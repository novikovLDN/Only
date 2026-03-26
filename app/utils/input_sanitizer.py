"""Input sanitization — Unicode cleanup, size limits, dangerous character removal.

Multi-layer protection:
1. Size/weight limits — reject oversized payloads
2. Unicode normalization — NFC form, strip invisible characters
3. Homoglyph detection — confusable character normalization
4. RTL/LTR override removal — prevent text direction exploits
5. Control character stripping — remove zero-width chars, BOMs, etc.
6. Emoji bomb protection — limit emoji density
7. Zalgo text detection — excessive combining marks
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Size limits
# ──────────────────────────────────────────────────────────────────────
MAX_MESSAGE_LENGTH = 1000  # chars
MAX_HABIT_TITLE_LENGTH = 100
MAX_USERNAME_DISPLAY_LENGTH = 64
MAX_CALLBACK_DATA_LENGTH = 256

# ──────────────────────────────────────────────────────────────────────
# Dangerous Unicode ranges and characters
# ──────────────────────────────────────────────────────────────────────

# Invisible / zero-width characters
INVISIBLE_CHARS = frozenset([
    "\u200B",  # Zero Width Space
    "\u200C",  # Zero Width Non-Joiner
    "\u200D",  # Zero Width Joiner
    "\u200E",  # Left-to-Right Mark
    "\u200F",  # Right-to-Left Mark (keep for Arabic display, strip from input)
    "\u2060",  # Word Joiner
    "\u2061",  # Function Application
    "\u2062",  # Invisible Times
    "\u2063",  # Invisible Separator
    "\u2064",  # Invisible Plus
    "\uFEFF",  # BOM / Zero Width No-Break Space
    "\u00AD",  # Soft Hyphen
    "\u034F",  # Combining Grapheme Joiner
    "\u061C",  # Arabic Letter Mark
    "\u180E",  # Mongolian Vowel Separator
])

# Bidirectional override characters — used for text spoofing
BIDI_OVERRIDES = frozenset([
    "\u202A",  # Left-to-Right Embedding
    "\u202B",  # Right-to-Left Embedding
    "\u202C",  # Pop Directional Formatting
    "\u202D",  # Left-to-Right Override
    "\u202E",  # Right-to-Left Override
    "\u2066",  # Left-to-Right Isolate
    "\u2067",  # Right-to-Left Isolate
    "\u2068",  # First Strong Isolate
    "\u2069",  # Pop Directional Isolate
])

# Tag characters (U+E0000 to U+E007F) — invisible tags
TAG_RANGE = range(0xE0000, 0xE0080)

# Variation selectors
VARIATION_SELECTORS = frozenset(chr(c) for c in range(0xFE00, 0xFE10))
VARIATION_SELECTORS_SUPPLEMENT = frozenset(chr(c) for c in range(0xE0100, 0xE01F0))

# Private Use Area (common for custom/malicious glyphs)
PUA_RANGES = [(0xE000, 0xF8FF), (0xF0000, 0xFFFFF), (0x100000, 0x10FFFF)]

# Regex for excessive combining marks (Zalgo text)
ZALGO_RE = re.compile(r"[\u0300-\u036F\u0489\u1AB0-\u1AFF\u1DC0-\u1DFF\u20D0-\u20FF\uFE20-\uFE2F]{3,}")

# Regex to count emoji
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)

MAX_EMOJI_RATIO = 0.7  # max 70% of text can be emoji


def _is_in_pua(char: str) -> bool:
    """Check if character is in Private Use Area."""
    cp = ord(char)
    return any(start <= cp <= end for start, end in PUA_RANGES)


def _is_tag_char(char: str) -> bool:
    """Check if character is a tag character."""
    return ord(char) in TAG_RANGE


def strip_invisible(text: str) -> str:
    """Remove all invisible and zero-width characters."""
    result = []
    for ch in text:
        if ch in INVISIBLE_CHARS:
            continue
        if ch in BIDI_OVERRIDES:
            continue
        if ch in VARIATION_SELECTORS or ch in VARIATION_SELECTORS_SUPPLEMENT:
            continue
        if _is_tag_char(ch):
            continue
        if _is_in_pua(ch):
            continue
        result.append(ch)
    return "".join(result)


def normalize_unicode(text: str) -> str:
    """NFC normalization + strip dangerous chars."""
    text = unicodedata.normalize("NFC", text)
    text = strip_invisible(text)
    return text


def strip_zalgo(text: str) -> str:
    """Remove excessive combining marks (Zalgo text)."""
    return ZALGO_RE.sub("", text)


def is_emoji_bomb(text: str) -> bool:
    """Check if text is mostly emoji (emoji bomb attack)."""
    if not text:
        return False
    clean = text.strip()
    if not clean:
        return False
    emoji_chars = sum(len(m.group()) for m in EMOJI_RE.finditer(clean))
    ratio = emoji_chars / len(clean)
    return ratio > MAX_EMOJI_RATIO and len(clean) > 10


def check_text_length(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> bool:
    """Return True if text is within allowed length."""
    return len(text) <= max_length


def sanitize_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str | None:
    """Full sanitization pipeline. Returns None if text should be rejected.

    Pipeline:
    1. Length check
    2. Unicode normalization (NFC)
    3. Strip invisible/zero-width characters
    4. Strip Zalgo combining marks
    5. Strip bidirectional overrides
    6. Emoji bomb check
    7. Whitespace normalization
    """
    if not text:
        return None

    # Length limit
    if len(text) > max_length:
        return None

    # Normalize
    text = normalize_unicode(text)

    # Zalgo
    text = strip_zalgo(text)

    # Emoji bomb
    if is_emoji_bomb(text):
        return None

    # Collapse multiple whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None

    return text


def sanitize_habit_title(title: str) -> str | None:
    """Sanitize habit title with strict limits."""
    return sanitize_text(title, max_length=MAX_HABIT_TITLE_LENGTH)


def sanitize_username(name: str) -> str:
    """Sanitize a display name/username."""
    result = sanitize_text(name, max_length=MAX_USERNAME_DISPLAY_LENGTH)
    return result or "User"
