import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.actions import ActionService
from app.api.router import api_router
from app.config import Settings, get_settings
from app.database import get_db, init_db
from app.errors import LlmDisabledError, ParserError
from app.parser import MessageParser
from app.scheduler import create_scheduler
from app.telegram import TelegramClient
from app.utils import normalize_incoming_chat_text, resolved_slash_command

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class SetWebhookRequest(BaseModel):
    url: HttpUrl


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    init_db()

    logger.info(
        "app_startup environment=%s database_url=%s",
        settings.environment,
        settings.database_url,
    )
    if settings.environment.strip().lower() in ("production", "prod"):
        dbu = settings.database_url
        if dbu.startswith("sqlite:///./") or dbu.startswith("sqlite:///@./"):
            logger.warning(
                "Relative DATABASE_URL (%s): data is NOT stored under mounted /app/data. "
                "Use DATABASE_URL=sqlite:////app/data/assistant.db and remove DATABASE_URL_LOCAL on the server.",
                dbu,
            )

    scheduler = create_scheduler(settings)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("app_started name=%s", settings.app_name)

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logger.info("app_stopped")


app = FastAPI(title="Telegram Personal Assistant", version="0.2.0", lifespan=lifespan)

_settings = get_settings()
if _settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    """Liveness for uptime monitors, Coolify healthchecks, and quick debugging."""
    return {
        "status": "ok",
        "service": request.app.title,
        "version": request.app.version,
    }


@app.head("/health")
def health_head() -> Response:
    """Lightweight probe (some monitors use HEAD to save bandwidth)."""
    return Response(status_code=200)


@app.post("/telegram/set-webhook")
async def set_webhook(
    payload: SetWebhookRequest,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    result = await TelegramClient(settings).set_webhook(str(payload.url))
    return {"ok": True, "telegram": result}


@app.post("/telegram/webhook")
@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    settings = get_settings()
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    logger.info("telegram_update update_id=%s", payload.get("update_id"))

    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return {"ok": True}

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = normalize_incoming_chat_text(message.get("text") or "")
    if not chat_id or not text:
        return {"ok": True}

    logger.info("telegram_message chat_id=%s text=%r", chat_id, text)
    telegram = TelegramClient(settings)

    if settings.allowed_telegram_ids and chat_id not in settings.allowed_telegram_ids:
        logger.warning("telegram_forbidden chat_id=%s", chat_id)
        await telegram.send_message(
            chat_id,
            "No tenés permiso para usar este bot. Si deberías tener acceso, pedile al administrador que agregue tu chat_id a ALLOWED_TELEGRAM_IDS.",
        )
        return {"ok": True}

    cmd = resolved_slash_command(message, text)
    if cmd in {"/start", "/help"}:
        response_text = (
            "Hola. Comandos: /g gasto, /i ingreso, /r recordatorio,\n"
            "/lr [hoy|mañana|semana|mes|1/6/26-15/6/26] (listar recordatorios pendientes).\n"
            "/get [mes] resumen del mes (ej. /get, /get mayo, /get 5/2026).\n"
            "/g importe categoría [fecha] — fecha al final tipo 25/5/26 o hoy/ayer.\n"
            "/i importe origen [fecha] — igual que /g.\n"
            "Lenguaje natural: requiere ENABLE_LLM_PARSER en el servidor (v2.0)."
        )
        await telegram.send_message(chat_id, response_text)
        logger.info("telegram_response chat_id=%s text=%r", chat_id, response_text)
        return {"ok": True}

    if cmd == "/get":
        _, _, get_body = text.partition(" ")
        try:
            response_text = ActionService(db, settings).format_monthly_report(
                chat_id, get_body.strip()
            )
        except ParserError as exc:
            response_text = str(exc)
        await telegram.send_message(chat_id, response_text)
        logger.info("telegram_response chat_id=%s text=%r", chat_id, response_text)
        return {"ok": True}

    try:
        action = await MessageParser(settings).parse_message(text)
        response_text = ActionService(db, settings).execute(chat_id, action)
    except LlmDisabledError as exc:
        logger.info("llm_disabled chat_id=%s", chat_id)
        response_text = str(exc)
    except ParserError as exc:
        logger.warning("parse_failed chat_id=%s error=%s", chat_id, exc)
        response_text = "No pude entenderlo. Probá con: /g 25000 comida"
    except Exception:
        logger.exception("message_processing_failed chat_id=%s", chat_id)
        response_text = "Tuve un problema guardando eso. Probá de nuevo."

    await telegram.send_message(chat_id, response_text)
    logger.info("telegram_response chat_id=%s text=%r", chat_id, response_text)
    return {"ok": True}


def _mount_frontend() -> None:
    if not FRONTEND_DIST.is_dir():
        logger.info("frontend_dist_missing path=%s", FRONTEND_DIST)
        return
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    index_file = FRONTEND_DIST / "index.html"

    @app.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "telegram/", "webhook/", "health")):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)


_mount_frontend()
