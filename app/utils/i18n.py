"""i18n utilities."""

from app.i18n.loader import get_texts, get_presets, get_weekdays


def t(key: str, lang: str | None, **kw) -> str:
    texts = get_texts(lang or "en")
    s = texts.get(key, key)
    return s.format(**kw) if kw else s
