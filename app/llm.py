import json
import logging
from datetime import datetime
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.config import Settings
from app.errors import ParserError

logger = logging.getLogger(__name__)


STRUCTURED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "intent",
        "amount",
        "category",
        "source",
        "date",
        "description",
        "datetime",
        "text",
        "tags",
        "query_type",
        "period",
    ],
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["expense", "income", "reminder", "note", "query", "unknown"],
        },
        "amount": {"anyOf": [{"type": "number"}, {"type": "null"}]},
        "category": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "source": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "description": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "datetime": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "text": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "tags": {
            "anyOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "null"},
            ]
        },
        "query_type": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [
                        "expenses_total",
                        "incomes_total",
                        "balance",
                        "reminders_list",
                        "notes_search",
                        "unknown",
                    ],
                },
                {"type": "null"},
            ]
        },
        "period": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": ["today", "week", "current_month", "month", "all"],
                },
                {"type": "null"},
            ]
        },
    },
}


SYSTEM_PROMPT = """Sos un parser JSON para un asistente personal por Telegram.
No converses, no expliques y no ejecutes lógica: solo clasificá el mensaje y devolvé JSON válido.

Intenciones:
- expense: gastos. Campos: amount, category, date, description.
- income: ingresos. Campos: amount, source, date, description.
- reminder: recordatorios/eventos. Campos: datetime, text.
- note: notas o ideas. Campos: text, tags.
- query: preguntas sobre datos guardados. Campos: query_type, period, text.
- unknown: si no hay suficiente información.

Reglas:
- Usá fechas relativas contra el "ahora" provisto por el usuario del sistema.
- Para expense/income, si no hay fecha explícita usá la fecha de hoy.
- Para reminder, devolvé datetime ISO 8601 local. Si falta hora, inferí 09:00.
- Normalizá importes a número: "luca/lucas" = 1000, "mil" = 1000, "palo/palos" = 1000000, "millón/millon" = 1000000.
- category/source deben ser cortos, en minúscula y sin artículos innecesarios.
- description conserva el detalle útil del mensaje.
- Para notas, tags debe ser una lista corta de etiquetas en minúscula.
- query_type válido: expenses_total, incomes_total, balance, reminders_list, notes_search.
- period válido: today, week, current_month, month, all. Si no está claro, usá current_month para dinero y all para recordatorios/notas.
- Campos no usados deben ir como null, salvo tags que puede ser null.
"""


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def parse(self, text: str, now: datetime) -> dict[str, Any]:
        if self.client is None:
            raise ParserError("OPENAI_API_KEY is not configured")

        user_prompt = (
            f"Ahora local: {now.isoformat()}\n"
            f"Zona horaria: {self.settings.app_timezone}\n"
            f"Mensaje de Telegram: {text}"
        )
        logger.info("llm_request text=%r", text)

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "personal_assistant_parse",
                        "strict": True,
                        "schema": STRUCTURED_OUTPUT_SCHEMA,
                    },
                },
                max_completion_tokens=300,
            )
        except OpenAIError as exc:
            logger.exception("llm_error")
            raise ParserError("No pude interpretar el mensaje ahora") from exc

        content = response.choices[0].message.content
        logger.info("llm_response content=%s", content)
        if not content:
            raise ParserError("Empty LLM response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ParserError("Invalid JSON returned by LLM") from exc

        return parsed
