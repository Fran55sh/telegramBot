from datetime import datetime

from app.config import Settings
from app.fallback import parse_fallback_command
from app.schemas import ExpenseAction, IncomeAction, ReminderAction


def test_expense_fallback_supports_lucas():
    settings = Settings()
    action = parse_fallback_command("/g 12 lucas tornillos", datetime(2026, 5, 9, 12, 0), settings)

    assert isinstance(action, ExpenseAction)
    assert action.amount == 12000
    assert action.category == "tornillos"


def test_income_fallback_supports_mil():
    settings = Settings()
    action = parse_fallback_command("/i 500 mil sueldo", datetime(2026, 5, 9, 12, 0), settings)

    assert isinstance(action, IncomeAction)
    assert action.amount == 500000
    assert action.source == "sueldo"


def test_reminder_fallback_supports_tomorrow_and_time():
    settings = Settings()
    action = parse_fallback_command("/r mañana 10am dentista", datetime(2026, 5, 9, 12, 0), settings)

    assert isinstance(action, ReminderAction)
    assert action.datetime == datetime(2026, 5, 10, 10, 0)
    assert action.text == "dentista"
