"""Parse month arguments for /get and similar commands."""

from datetime import date

from app.errors import ParserError

MONTH_NAMES: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def month_title(year: int, month: int) -> str:
    for name, num in MONTH_NAMES.items():
        if num == month:
            return f"{name.capitalize()} {year}"
    return f"{month:02d}/{year}"


def parse_month_arg(arg: str, today: date) -> tuple[int, int]:
    """
    Parse /get month argument into (year, month).
    Empty arg → current month. Accepts: mayo, 5, 5/2026, 2026-05, 05-2026.
    """
    text = arg.strip().lower()
    if not text:
        return today.year, today.month

    if text in MONTH_NAMES:
        return today.year, MONTH_NAMES[text]

    if "/" in text:
        left, _, right = text.partition("/")
        left = left.strip()
        right = right.strip()
        if left.isdigit() and right.isdigit():
            m, y = int(left), int(right)
            if m > 12:
                m, y = y, m
            if y < 100:
                y += 2000
            return _validate_month(y, m)
        raise ParserError("Mes no válido. Ej: /get mayo, /get 5, /get 5/2026")

    if "-" in text:
        parts = text.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            a, b = int(parts[0]), int(parts[1])
            if a > 12:
                return _validate_month(a, b)
            return _validate_month(b, a)
        raise ParserError("Mes no válido. Ej: /get 2026-05")

    if text.isdigit():
        value = int(text)
        if 1900 <= value <= 2100:
            raise ParserError("Indicá también el mes. Ej: /get 5/2026")
        if 1 <= value <= 12:
            return today.year, value
        raise ParserError("Mes no válido (1-12). Ej: /get 5")

    raise ParserError("Mes no reconocido. Ej: /get mayo, /get 5, /get 5/2026")


def _validate_month(year: int, month: int) -> tuple[int, int]:
    if not (1 <= month <= 12):
        raise ParserError("Mes debe estar entre 1 y 12")
    if not (2000 <= year <= 2100):
        raise ParserError("Año no válido")
    return year, month
