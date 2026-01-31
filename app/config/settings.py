"""
Application settings loaded from environment.
"""

import os
from functools import lru_cache
from typing import Sequence

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Bot
    bot_token: str = ""
    bot_username: str = ""  # Without @, for referral links
    admin_ids: str = ""
    alert_chat_id: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/habitbot"

    # Payments
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_webhook_secret: str = ""
    cryptobot_token: str = ""

    # Limits
    trial_days: int = 7
    free_habits_limit: int = 5
    premium_habits_limit: int = 999
    rate_limit_per_minute: int = 30

    # Monitoring
    sentry_dsn: str = ""
    health_check_port: int = 8080

    @property
    def http_port(self) -> int:
        """Port for HTTP server (health). Railway sets PORT; use it when present."""
        port = os.environ.get("PORT")
        if port is not None:
            try:
                return int(port)
            except ValueError:
                pass
        return self.health_check_port

    # Deployment (Railway: set scale=1, BOT_INSTANCE_ROLE=primary)
    railway_environment: str = ""
    bot_instance_role: str = ""  # "primary" = may run; other/no-value = primary allowed

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str | None) -> str:
        """Ensure postgresql+asyncpg:// for async SQLAlchemy (Railway may provide postgresql://)."""
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/habitbot"
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("admin_ids", "alert_chat_id", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str) -> str:
        """Keep as string for parsing in property."""
        return v or ""

    @property
    def admin_id_list(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def alert_chat_id_int(self) -> int | None:
        """Alert chat ID as int or None."""
        if not self.alert_chat_id:
            return None
        return int(self.alert_chat_id.strip())

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_id_list


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
