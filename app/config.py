from functools import lru_cache
from typing import Final, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Persisted storage in Docker / Coolify: mount a volume here. DATABASE_URL must use this path there.
DATA_DIR: Final[str] = "/app/data"


class Settings(BaseSettings):
    """Centralized application settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "telegram-personal-assistant"
    app_timezone: str = "America/Argentina/Buenos_Aires"
    log_level: str = "INFO"

    #: development | dev | local => prefer DATABASE_URL_LOCAL when set; production | prod => DATABASE_URL only
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    #: Used in production (`ENVIRONMENT=production`) and as fallback locally if DATABASE_URL_LOCAL is empty
    database_url: str = Field(default="sqlite:///./assistant.db", validation_alias="DATABASE_URL")

    #: Optional local-only DB URL; overrides DATABASE_URL when not in production
    database_url_local: str = Field(default="", validation_alias="DATABASE_URL_LOCAL")

    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="", validation_alias="TELEGRAM_WEBHOOK_SECRET")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", validation_alias="OPENAI_MODEL")

    enable_llm_parser: bool = Field(default=False, validation_alias="ENABLE_LLM_PARSER")

    allowed_telegram_ids_csv: str = Field(default="", validation_alias="ALLOWED_TELEGRAM_IDS")

    reminder_check_seconds: int = 60

    @model_validator(mode="after")
    def resolve_database_url_for_environment(self) -> Self:
        env = self.environment.strip().lower()
        if env in ("production", "prod"):
            return self
        local = self.database_url_local.strip()
        if local:
            self.database_url = local
        return self

    @property
    def allowed_telegram_ids(self) -> list[int]:
        text = self.allowed_telegram_ids_csv.strip()
        if not text:
            return []
        out: list[int] = []
        for part in text.split(","):
            part = part.strip()
            if part:
                out.append(int(part))
        return out

    @property
    def telegram_api_base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.telegram_bot_token}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
