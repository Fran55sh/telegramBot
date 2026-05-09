import logging

from pydantic import ValidationError

from app.config import Settings
from app.errors import ParserError
from app.fallback import is_fallback_command, parse_fallback_command
from app.llm import LLMService
from app.schemas import Action, validate_action
from app.utils import local_now

logger = logging.getLogger(__name__)


class MessageParser:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMService(settings)

    async def parse_message(self, text: str) -> Action:
        now = local_now(self.settings)

        if is_fallback_command(text):
            logger.info("fallback_parse text=%r", text)
            return parse_fallback_command(text, now, self.settings)

        raw = await self.llm.parse(text, now)
        try:
            return validate_action(raw, now, self.settings)
        except (ValidationError, ParserError) as exc:
            logger.warning("invalid_structured_output raw=%s error=%s", raw, exc)
            raise ParserError("No pude convertir el mensaje en una acción válida") from exc
