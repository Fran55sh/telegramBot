import asyncio

import pytest

from app.config import Settings
from app.errors import LlmDisabledError
from app.parser import MessageParser


def test_llm_disabled_raises_for_free_text():
    settings = Settings(enable_llm_parser=False)
    parser = MessageParser(settings)

    with pytest.raises(LlmDisabledError):
        asyncio.run(parser.parse_message("gasté 500 en pan"))


def test_llm_disabled_allows_fallback_commands():
    settings = Settings(enable_llm_parser=False)
    parser = MessageParser(settings)

    action = asyncio.run(parser.parse_message("/g 100 pan"))
    assert action.intent == "expense"
