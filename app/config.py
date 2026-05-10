from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "telegram-personal-assistant"
    app_timezone: str = "America/Argentina/Buenos_Aires"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./assistant.db"

    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="", validation_alias="TELEGRAM_WEBHOOK_SECRET")

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", validation_alias="OPENAI_MODEL")

    enable_llm_parser: bool = Field(default=False, validation_alias="ENABLE_LLM_PARSER")

    allowed_telegram_ids_csv: str = Field(default="", validation_alias="ALLOWED_TELEGRAM_IDS")

    reminder_check_seconds: int = 60

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
