import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_message(self, chat_id: int, text: str) -> None:
        if not self.settings.telegram_bot_token:
            logger.warning("telegram_bot_token_missing chat_id=%s text=%r", chat_id, text)
            return

        payload = {"chat_id": chat_id, "text": text}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.settings.telegram_api_base_url}/sendMessage", json=payload)
            response.raise_for_status()

    async def set_webhook(self, url: str) -> dict:
        if not self.settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        payload = {"url": url}
        if self.settings.telegram_webhook_secret:
            payload["secret_token"] = self.settings.telegram_webhook_secret

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.settings.telegram_api_base_url}/setWebhook", json=payload)
            response.raise_for_status()
            return response.json()
