from datetime import date

import pytest

from app.periods import period_label, resolve_date_range


def test_resolve_tomorrow():
    today = date(2026, 5, 26)
    start, end = resolve_date_range("tomorrow", today)
    assert start == date(2026, 5, 27)
    assert end == date(2026, 5, 28)


def test_resolve_next_week_starts_on_monday():
    today = date(2026, 5, 26)  # Tuesday
    start, end = resolve_date_range("next_week", today)
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 8)


def test_resolve_range_inclusive_end_day():
    start, end = resolve_date_range(
        "range",
        date(2026, 5, 1),
        date_from=date(2026, 6, 10),
        date_to=date(2026, 6, 15),
    )
    assert start == date(2026, 6, 10)
    assert end == date(2026, 6, 16)


def test_resolve_range_rejects_inverted_bounds():
    with pytest.raises(ValueError):
        resolve_date_range(
            "range",
            date(2026, 5, 1),
            date_from=date(2026, 6, 20),
            date_to=date(2026, 6, 1),
        )


def test_period_label_range():
    assert "10/06/2026" in period_label(
        "range",
        date_from=date(2026, 6, 10),
        date_to=date(2026, 6, 15),
    )
