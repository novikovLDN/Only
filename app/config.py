"""Application configuration."""

import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/habitbot"
    payment_provider_token: str = ""  # YooKassa LIVE token from @BotFather → Payments

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str | None) -> str:
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/habitbot"
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v or "postgresql+asyncpg://postgres:postgres@localhost:5432/habitbot"

    @property
    def http_port(self) -> int:
        return int(os.environ.get("PORT", "8080"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
ADMIN_ID = 6214188086
