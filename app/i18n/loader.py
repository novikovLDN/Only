"""i18n loader — delegates to app.utils.i18n."""

from app.utils.i18n import (
    TRANSLATIONS,
    get_presets,
    get_weekdays,
    t as t_fn,
)


def get_texts(lang: str | None) -> dict:
    return TRANSLATIONS.get(lang or "en", TRANSLATIONS["en"])


def t(key: str, lang: str | None, **kw) -> str:
    return t_fn(lang or "en", key, **kw)
