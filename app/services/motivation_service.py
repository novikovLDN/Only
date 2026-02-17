"""Motivation phrase service — get random, reset when exhausted."""

from app.repositories.motivation_repo import MotivationRepository


class MotivationService:
    def __init__(self, repo: MotivationRepository):
        self.repo = repo

    async def get_random_phrase(self, language: str) -> str:
        lang = language if language in ("ru", "en", "ar") else "ru"
        phrase = await self.repo.get_random_unused(lang)
        if phrase is None:
            await self.repo.reset_all_for_language(lang)
            phrase = await self.repo.get_random_unused(lang)
        if phrase is None:
            return "Молодец!" if lang == "ru" else ("أحسنت!" if lang == "ar" else "Well done!")
        await self.repo.mark_used(phrase)
        return phrase.text
