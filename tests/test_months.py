from datetime import date

import pytest

from app.errors import ParserError
from app.months import parse_month_arg


def test_parse_empty_is_current_month():
    today = date(2026, 5, 26)
    assert parse_month_arg("", today) == (2026, 5)


def test_parse_spanish_month_name():
    assert parse_month_arg("mayo", date(2026, 5, 26)) == (2026, 5)


def test_parse_month_year_slash():
    assert parse_month_arg("5/2025", date(2026, 5, 26)) == (2025, 5)


def test_parse_iso_month():
    assert parse_month_arg("2025-05", date(2026, 5, 26)) == (2025, 5)


def test_parse_invalid_month_raises():
    with pytest.raises(ParserError):
        parse_month_arg("trece", date(2026, 5, 26))
