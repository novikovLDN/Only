"""i18n loader — delegates to app.utils.i18n."""

from app.utils.i18n import (
    TRANSLATIONS,
    get_presets,
    get_weekdays,
    t as t_fn,
)


def get_texts(lang: str | None) -> dict:
    code = (lang or "en")[:2].lower()
    if code not in ("ru", "en", "ar"):
        code = "en"
    return TRANSLATIONS.get(code, TRANSLATIONS["ru"])


def t(key: str, lang: str | None, **kw) -> str:
    code = (lang or "en")[:2].lower()
    if code not in ("ru", "en", "ar"):
        code = "en"
    return t_fn(code, key, **kw)
