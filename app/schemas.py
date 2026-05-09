from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Settings
from app.errors import ParserError
from app.utils import parse_iso_date, parse_iso_datetime, to_naive_local

Intent = Literal["expense", "income", "reminder", "note", "query", "unknown"]
QueryType = Literal[
    "expenses_total",
    "incomes_total",
    "balance",
    "reminders_list",
    "notes_search",
    "unknown",
]
Period = Literal["today", "week", "current_month", "month", "all"]


class RawParsedMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    amount: Decimal | None = None
    category: str | None = None
    source: str | None = None
    date: str | None = None
    description: str | None = None
    datetime: str | None = None
    text: str | None = None
    tags: list[str] | None = None
    query_type: QueryType | None = None
    period: Period | None = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("amount must be positive")
        return value


class ExpenseAction(BaseModel):
    intent: Literal["expense"] = "expense"
    amount: Decimal
    category: str
    date: date
    description: str | None = None


class IncomeAction(BaseModel):
    intent: Literal["income"] = "income"
    amount: Decimal
    source: str
    date: date
    description: str | None = None


class ReminderAction(BaseModel):
    intent: Literal["reminder"] = "reminder"
    datetime: datetime
    text: str


class NoteAction(BaseModel):
    intent: Literal["note"] = "note"
    text: str
    tags: list[str] = Field(default_factory=list)


class QueryAction(BaseModel):
    intent: Literal["query"] = "query"
    query_type: QueryType
    period: Period = "current_month"
    text: str | None = None


Action = ExpenseAction | IncomeAction | ReminderAction | NoteAction | QueryAction


def _require_text(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ParserError(f"Missing required field: {field_name}")
    return value.strip()


def _parse_action_date(raw_date: str | None, today: date) -> date:
    if not raw_date:
        return today
    try:
        return parse_iso_date(raw_date)
    except ValueError as exc:
        raise ParserError("Invalid date format; expected YYYY-MM-DD") from exc


def validate_action(data: dict | RawParsedMessage, now: datetime, settings: Settings) -> Action:
    raw = data if isinstance(data, RawParsedMessage) else RawParsedMessage.model_validate(data)
    today = now.date()

    if raw.intent == "expense":
        if raw.amount is None:
            raise ParserError("Missing required field: amount")
        return ExpenseAction(
            amount=raw.amount,
            category=_require_text(raw.category, "category").lower(),
            date=_parse_action_date(raw.date, today),
            description=raw.description.strip() if raw.description else None,
        )

    if raw.intent == "income":
        if raw.amount is None:
            raise ParserError("Missing required field: amount")
        return IncomeAction(
            amount=raw.amount,
            source=_require_text(raw.source, "source").lower(),
            date=_parse_action_date(raw.date, today),
            description=raw.description.strip() if raw.description else None,
        )

    if raw.intent == "reminder":
        reminder_text = _require_text(raw.text, "text")
        if not raw.datetime:
            raise ParserError("Missing required field: datetime")
        try:
            remind_at = parse_iso_datetime(raw.datetime, settings)
        except ValueError as exc:
            raise ParserError("Invalid datetime format; expected ISO 8601") from exc
        now_naive = to_naive_local(now, settings)
        if remind_at <= now_naive:
            raise ParserError("Reminder datetime must be in the future")
        return ReminderAction(datetime=remind_at, text=reminder_text)

    if raw.intent == "note":
        tags = [tag.strip().lower() for tag in (raw.tags or []) if tag.strip()]
        return NoteAction(text=_require_text(raw.text, "text"), tags=tags)

    if raw.intent == "query":
        if raw.query_type is None or raw.query_type == "unknown":
            raise ParserError("Missing required field: query_type")
        default_period = "all" if raw.query_type in {"reminders_list", "notes_search"} else "current_month"
        return QueryAction(
            query_type=raw.query_type,
            period=raw.period or default_period,
            text=raw.text.strip() if raw.text else None,
        )

    raise ParserError("No pude entender el mensaje")
