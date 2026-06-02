from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db


@dataclass(frozen=True)
class ApiUser:
    chat_id: int


def get_api_user(
    authorization: str | None = Header(default=None),
    x_telegram_chat_id: str | None = Header(default=None, alias="X-Telegram-Chat-Id"),
    settings: Settings = Depends(get_settings),
) -> ApiUser:
    if not settings.web_app_token:
        raise HTTPException(status_code=503, detail="WEB_APP_TOKEN not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.web_app_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not x_telegram_chat_id:
        raise HTTPException(status_code=400, detail="Missing X-Telegram-Chat-Id header")
    try:
        chat_id = int(x_telegram_chat_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-Telegram-Chat-Id") from exc
    if settings.allowed_telegram_ids and chat_id not in settings.allowed_telegram_ids:
        raise HTTPException(status_code=403, detail="Chat not allowed")
    return ApiUser(chat_id=chat_id)


def db_session(db: Session = Depends(get_db)) -> Session:
    return db
