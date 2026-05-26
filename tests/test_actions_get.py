from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from app.actions import ActionService
from app.config import Settings
from app.models import Expense, Income


def _expense(amount: str, category: str, day: int, desc: str | None = None) -> Expense:
    return Expense(
        id=1,
        chat_id=99,
        amount=Decimal(amount),
        category=category,
        date=date(2026, 5, day),
        description=desc,
    )


def _income(amount: str, source: str, day: int) -> Income:
    return Income(
        id=1,
        chat_id=99,
        amount=Decimal(amount),
        source=source,
        date=date(2026, 5, day),
        description=None,
    )


def test_format_monthly_report_groups_expenses(monkeypatch):
    monkeypatch.setattr(
        "app.actions.local_now",
        lambda _settings: __import__("datetime").datetime(2026, 5, 26, 12, 0),
    )
    incomes = [_income("1500", "sueldo", 5)]
    expenses = [_expense("500", "supermercado", 10), _expense("200", "restaurantes", 12)]

    r_incomes = MagicMock()
    r_incomes.scalars.return_value.all.return_value = incomes
    r_expenses = MagicMock()
    r_expenses.scalars.return_value.all.return_value = expenses
    db = MagicMock()
    db.execute.side_effect = [r_incomes, r_expenses]

    svc = ActionService(db, Settings(_env_file=None, environment="development"))
    out = svc.format_monthly_report(99, "")

    assert "Mayo 2026" in out
    assert "Ingresos: $1.500" in out
    assert "Egresos: $700" in out
    assert " - supermercado $500" in out
    assert "71,4%" in out
    assert " - restaurantes $200" in out
    assert "28,6%" in out
    assert "Balance: $800" in out


def test_format_monthly_report_empty_month(monkeypatch):
    monkeypatch.setattr(
        "app.actions.local_now",
        lambda _settings: __import__("datetime").datetime(2026, 5, 26, 12, 0),
    )
    empty = MagicMock()
    empty.scalars.return_value.all.return_value = []
    db = MagicMock()
    db.execute.side_effect = [empty, empty]

    svc = ActionService(db, Settings(_env_file=None, environment="development"))
    out = svc.format_monthly_report(99, "mayo")

    assert "No hay movimientos" in out
