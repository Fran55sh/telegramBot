from app.utils import normalize_telegram_command_text


def test_normalize_removes_leading_bom_so_get_matches():
    text = normalize_telegram_command_text("\ufeff/get")
    assert text == "/get"


def test_normalize_strips_bidi_then_command():
    text = normalize_telegram_command_text("\u200e/get")
    assert text == "/get"
