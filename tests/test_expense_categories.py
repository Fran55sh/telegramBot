from app.expense_categories import normalize_expense_category, parse_category_from_text


def test_normalize_known_subcategory():
    assert normalize_expense_category("supermercado") == "supermercado"
    assert normalize_expense_category("cafetería") == "cafeteria"


def test_normalize_alias():
    assert normalize_expense_category("nafta") == "combustible"


def test_normalize_unknown_goes_to_sin_clasificar():
    assert normalize_expense_category("cosa rara") == "sin-clasificar"


def test_parse_multiword_category():
    cat, desc = parse_category_from_text("mantenimiento vehiculo taller")
    assert cat == "mantenimiento-vehiculo"
    assert desc == "taller"
