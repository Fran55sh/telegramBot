class ParserError(Exception):
    """Raised when a user message cannot be converted into a valid action."""


class LlmDisabledError(ParserError):
    """Raised when natural-language parsing is disabled and the message is not a slash command."""

    USER_MESSAGE = (
        "Por ahora solo se aceptan comandos: "
        "/g importe categoría, /i importe origen, /r texto [fecha u hora], /get (totales). "
        "Activá ENABLE_LLM_PARSER en el servidor para lenguaje natural (v2.0)."
    )

    def __init__(self, message: str | None = None):
        super().__init__(message or self.USER_MESSAGE)
