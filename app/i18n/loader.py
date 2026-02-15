"""i18n loader."""

from app.i18n.en import HABIT_PRESETS as EN_PRESETS
from app.i18n.en import TEXTS as EN_TEXTS
from app.i18n.en import WEEKDAYS as EN_WEEKDAYS
from app.i18n.ru import HABIT_PRESETS as RU_PRESETS
from app.i18n.ru import TEXTS as RU_TEXTS
from app.i18n.ru import WEEKDAYS as RU_WEEKDAYS


def get_texts(lang: str | None) -> dict:
    return RU_TEXTS if lang == "ru" else EN_TEXTS


def t(key: str, lang: str | None, **kw) -> str:
    texts = get_texts(lang or "en")
    s = texts.get(key, key)
    return s.format(**kw) if kw else s


def get_presets(lang: str) -> list[str]:
    return RU_PRESETS if lang == "ru" else EN_PRESETS


def get_weekdays(lang: str) -> list[str]:
    return RU_WEEKDAYS if lang == "ru" else EN_WEEKDAYS
