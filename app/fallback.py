import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.config import Settings
from app.errors import ParserError
from app.schemas import ExpenseAction, IncomeAction, ReminderAction
from app.utils import parse_decimal, to_naive_local

AMOUNT_MULTIPLIERS = {
    "k": Decimal("1000"),
    "mil": Decimal("1000"),
    "luca": Decimal("1000"),
    "lucas": Decimal("1000"),
    "palo": Decimal("1000000"),
    "palos": Decimal("1000000"),
    "millon": Decimal("1000000"),
    "millones": Decimal("1000000"),
    "millón": Decimal("1000000"),
}

TIME_RE = re.compile(
    r"\b(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)\b"
    r"|\b(?P<hour24>\d{1,2}):(?P<minute24>\d{2})\b",
    re.I,
)

TRAILING_DMY_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$")


def is_fallback_command(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered.startswith("/g ") or lowered.startswith("/i ") or lowered.startswith("/r ")


def parse_fallback_command(text: str, now: datetime, settings: Settings):
    now_naive = to_naive_local(now, settings)
    stripped = text.strip()
    command, _, body = stripped.partition(" ")
    body = body.strip()
    if not body:
        raise ParserError("El comando está vacío")

    if command.lower() == "/g":
        amount, rest = _extract_amount(body)
        tx_date, rest = _extract_relative_date(rest, now_naive)
        category = _first_word(rest, "category")
        return ExpenseAction(amount=amount, category=category.lower(), date=tx_date, description=rest)

    if command.lower() == "/i":
        amount, rest = _extract_amount(body)
        tx_date, rest = _extract_relative_date(rest, now_naive)
        source = _first_word(rest, "source")
        return IncomeAction(amount=amount, source=source.lower(), date=tx_date, description=rest)

    if command.lower() == "/r":
        remind_at, reminder_text = _parse_reminder_body(body, now_naive)
        if remind_at <= now_naive:
            raise ParserError("El recordatorio debe ser a futuro")
        return ReminderAction(datetime=remind_at, text=reminder_text)

    raise ParserError("Comando no soportado")


def _extract_amount(body: str) -> tuple[Decimal, str]:
    parts = body.split()
    if not parts:
        raise ParserError("Falta el importe")

    try:
        amount = parse_decimal(parts[0])
    except ValueError as exc:
        raise ParserError("No pude leer el importe") from exc

    rest_start = 1
    if len(parts) > 1:
        multiplier = AMOUNT_MULTIPLIERS.get(_strip_accents(parts[1].lower()))
        if multiplier:
            amount *= multiplier
            rest_start = 2

    rest = " ".join(parts[rest_start:]).strip()
    if amount <= 0:
        raise ParserError("El importe debe ser positivo")
    if not rest:
        raise ParserError("Falta una categoría o descripción")
    return amount, rest


def _extract_relative_date(text: str, now: datetime) -> tuple:
    lowered = text.lower()
    tx_date = now.date()
    replacements = {
        "antes de ayer": -2,
        "anteayer": -2,
        "ayer": -1,
        "hoy": 0,
    }
    for marker, days in replacements.items():
        pattern = rf"\b{re.escape(marker)}\b"
        if re.search(pattern, lowered):
            tx_date = (now + timedelta(days=days)).date()
            text = re.sub(pattern, "", text, flags=re.I).strip()
            break
    return tx_date, " ".join(text.split())


def _extract_trailing_dmy(text: str) -> tuple[date, str] | None:
    """Parse D/M/Y or D/M/YY at end of string; returns (date, text_without_date)."""
    stripped = text.strip()
    match = TRAILING_DMY_RE.search(stripped)
    if not match:
        return None
    day_s, month_s, year_s = match.group(1), match.group(2), match.group(3)
    day, month = int(day_s), int(month_s)
    year = int(year_s)
    if year < 100:
        year += 2000
    try:
        target = date(year, month, day)
    except ValueError as exc:
        raise ParserError("La fecha no es válida") from exc
    rest = stripped[: match.start()].strip()
    return target, rest


def _parse_reminder_body(body: str, now: datetime) -> tuple[datetime, str]:
    text = body.strip()
    target_date: date | None = None
    explicit = _extract_trailing_dmy(text)
    if explicit is not None:
        target_date, text = explicit
    else:
        lowered = text.lower()

        relative_dates = [
            ("pasado mañana", 2),
            ("pasado manana", 2),
            ("mañana", 1),
            ("manana", 1),
            ("hoy", 0),
        ]
        for marker, days in relative_dates:
            if re.search(rf"\b{marker}\b", lowered):
                target_date = (now + timedelta(days=days)).date()
                text = re.sub(rf"\b{marker}\b", "", text, flags=re.I).strip()
                break

    if target_date is None:
        target_date = now.date()

    target_time = time(hour=9, minute=0)
    match = TIME_RE.search(text)
    if match:
        hour = int(match.group("hour") or match.group("hour24"))
        minute = int(match.group("minute") or match.group("minute24") or 0)
        ampm = (match.group("ampm") or "").lower()
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        if hour > 23 or minute > 59:
            raise ParserError("La hora del recordatorio no es válida")
        target_time = time(hour=hour, minute=minute)
        text = (text[: match.start()] + text[match.end() :]).strip()

    reminder_text = " ".join(text.split())
    if not reminder_text:
        raise ParserError("Falta el texto del recordatorio")
    return datetime.combine(target_date, target_time), reminder_text


def _first_word(text: str, field_name: str) -> str:
    if not text.strip():
        raise ParserError(f"Missing required field: {field_name}")
    return text.split()[0]


def _strip_accents(value: str) -> str:
    return (
        value.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
