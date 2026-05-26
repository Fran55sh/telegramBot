"""Resolve calendar periods to half-open local date ranges [start, end)."""

from datetime import date, timedelta

from app.utils import format_date

PeriodKey = str

PERIOD_LABELS: dict[str, str] = {
    "today": "hoy",
    "tomorrow": "mañana",
    "week": "esta semana",
    "next_week": "la próxima semana",
    "current_month": "este mes",
    "month": "este mes",
    "next_month": "el próximo mes",
    "all": "todos los pendientes",
}


def period_label(
    period: PeriodKey,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> str:
    if period == "range" and date_from and date_to:
        return f"del {format_date(date_from)} al {format_date(date_to)}"
    return PERIOD_LABELS.get(period, period)


def resolve_date_range(
    period: PeriodKey,
    today: date,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[date, date] | None:
    """
    Return [start, end) calendar dates for a period, or None when no extra filter applies.

    For ``range``, both bounds are inclusive calendar days; the returned end is exclusive
    (midnight after the last included day).
    """
    if period == "all":
        return None

    if period == "range":
        if date_from is None or date_to is None:
            raise ValueError("range period requires date_from and date_to")
        if date_to < date_from:
            raise ValueError("date_to must not be before date_from")
        return date_from, date_to + timedelta(days=1)

    if period == "today":
        return today, today + timedelta(days=1)

    if period == "tomorrow":
        day = today + timedelta(days=1)
        return day, day + timedelta(days=1)

    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=7)

    if period == "next_week":
        start = today - timedelta(days=today.weekday()) + timedelta(days=7)
        return start, start + timedelta(days=7)

    if period in {"current_month", "month"}:
        return _month_range(today.replace(day=1))

    if period == "next_month":
        this_month = today.replace(day=1)
        if this_month.month == 12:
            return _month_range(this_month.replace(year=this_month.year + 1, month=1))
        return _month_range(this_month.replace(month=this_month.month + 1))

    return None


def _month_range(month_start: date) -> tuple[date, date]:
    if month_start.month == 12:
        end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        end = month_start.replace(month=month_start.month + 1)
    return month_start, end
