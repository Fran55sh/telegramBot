from app.utils import (
    normalize_incoming_chat_text,
    normalize_telegram_command_text,
    resolved_slash_command,
)


def test_normalize_removes_leading_bom_so_get_matches():
    text = normalize_telegram_command_text("\ufeff/get")
    assert text == "/get"


def test_normalize_strips_bidi_then_command():
    text = normalize_telegram_command_text("\u200e/get")
    assert text == "/get"


def test_incoming_nfkc_maps_fullwidth_slash_get():
    assert normalize_incoming_chat_text("\uff0fget") == "/get"


def test_resolved_get_without_entities_after_nfkc():
    raw = "\uff0fget"
    norm = normalize_incoming_chat_text(raw)
    msg = {"text": raw}
    assert resolved_slash_command(msg, norm) == "/get"


def test_resolved_uses_bot_command_entity_with_utf16_prefix():
    raw = "\U0001f914 /get"
    norm = normalize_incoming_chat_text(raw)

    def utf16_units(fragment: str) -> int:
        return len(fragment.encode("utf-16-le")) // 2

    off = utf16_units("\U0001f914 ")
    ln = utf16_units("/get")
    msg = {
        "text": raw,
        "entities": [{"type": "bot_command", "offset": off, "length": ln}],
    }
    assert resolved_slash_command(msg, norm) == "/get"
