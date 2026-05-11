from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from app.config import Settings

# BOM / ZWSP / bidi marks some Telegram clients prepend to message text.
_TELEGRAM_LEADING_JUNK = frozenset(
    "\ufeff\u200b\u200c\u200d\u2060\u200e\u200f\u202a\u202c"
)


def normalize_telegram_command_text(text: str) -> str:
    """Strip whitespace and invisible leading characters from user text."""
    t = text.strip()
    while t and t[0] in _TELEGRAM_LEADING_JUNK:
        t = t[1:].lstrip()
    return t.strip()


def local_now(settings: Settings) -> datetime:
    return datetime.now(ZoneInfo(settings.app_timezone))


def to_naive_local(value: datetime, settings: Settings) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(ZoneInfo(settings.app_timezone)).replace(tzinfo=None)


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def parse_iso_datetime(value: str, settings: Settings) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return to_naive_local(parsed, settings)


def parse_decimal(value: str) -> Decimal:
    cleaned = (
        value.strip()
        .lower()
        .replace("$", "")
        .replace("ars", "")
        .replace(" ", "")
    )
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned and len(cleaned.rsplit(".", 1)[-1]) == 3:
        cleaned = cleaned.replace(".", "")

    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount: {value}") from exc


def format_money(amount: Decimal | float | int) -> str:
    decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    if decimal_amount == decimal_amount.to_integral_value():
        number = f"{int(decimal_amount):,}".replace(",", ".")
    else:
        number = f"{decimal_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${number}"


def format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def format_datetime(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M")
