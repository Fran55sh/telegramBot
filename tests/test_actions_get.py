from decimal import Decimal
from unittest.mock import MagicMock

from app.actions import ActionService
from app.config import Settings


def test_format_lifetime_totals_money():
    r1 = MagicMock()
    r1.scalar_one.return_value = Decimal("1500")
    r2 = MagicMock()
    r2.scalar_one.return_value = Decimal("400")
    db = MagicMock()
    db.execute.side_effect = [r1, r2]

    svc = ActionService(db, Settings(_env_file=None, environment="development"))
    out = svc.format_lifetime_totals(99)

    assert "Ingresos:" in out
    assert "Egresos:" in out
    assert "$1.500" in out
    assert "$400" in out
