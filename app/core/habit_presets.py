"""Bilingual habit presets (RU/EN)."""

HABIT_PRESETS = [
    {"id": 1, "ru": "🏃‍♂️ Бег", "en": "🏃‍♂️ Running"},
    {"id": 2, "ru": "📚 Чтение", "en": "📚 Reading"},
    {"id": 3, "ru": "🧘 Медитация", "en": "🧘 Meditation"},
    {"id": 4, "ru": "💧 Пить воду", "en": "💧 Drink water"},
    {"id": 5, "ru": "💪 Тренировка", "en": "💪 Workout"},
    {"id": 6, "ru": "🌅 Ранний подъём", "en": "🌅 Wake up early"},
    {"id": 7, "ru": "📝 Дневник", "en": "📝 Journaling"},
    {"id": 8, "ru": "📵 Без соцсетей", "en": "📵 No social media"},
    {"id": 9, "ru": "🥗 Правильное питание", "en": "🥗 Healthy eating"},
    {"id": 10, "ru": "🚶 Прогулка", "en": "🚶 Walk"},
    {"id": 11, "ru": "📖 Учёба", "en": "📖 Study"},
    {"id": 12, "ru": "💤 Ложиться вовремя", "en": "💤 Sleep on time"},
    {"id": 13, "ru": "🧠 Изучать язык", "en": "🧠 Learn language"},
    {"id": 14, "ru": "🎯 Планирование", "en": "🎯 Planning"},
    {"id": 15, "ru": "💰 Учёт расходов", "en": "💰 Track expenses"},
    {"id": 16, "ru": "📷 Фото дня", "en": "📷 Photo of the day"},
    {"id": 17, "ru": "🙏 Благодарность", "en": "🙏 Gratitude"},
    {"id": 18, "ru": "🧹 Уборка", "en": "🧹 Cleaning"},
    {"id": 19, "ru": "🧘‍♀️ Растяжка", "en": "🧘‍♀️ Stretching"},
    {"id": 20, "ru": "🎵 Практика навыка", "en": "🎵 Skill practice"},
]

FREE_PRESET_LIMIT = 3  # presets with id <= 3 are free


def get_preset_title(preset_id: int, lang: str) -> str:
    """Get preset title by id and language. Returns empty string if not found."""
    lang = "en" if (lang or "").lower() == "en" else "ru"
    for p in HABIT_PRESETS:
        if p["id"] == preset_id:
            return p.get(lang, p["ru"])
    return ""
