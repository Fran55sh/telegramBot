# Telegram Personal Assistant — System Overview

## Purpose

**Telegram bot** for **expenses**, **incomes**, **reminders**, and **notes**, scoped per Telegram **`chat_id`** (several users can use the same bot without sharing rows). Optional env **`ALLOWED_TELEGRAM_IDS`** restricts which chats may invoke the bot. **Natural language** is parsed with OpenAI only when **`ENABLE_LLM_PARSER=true`** (v2.0); by default only slash commands **`/g`**, **`/i`**, **`/r`** are handled without the LLM.

**Explicitly out of scope in this version:** LangChain, agents, conversational memory, microservices, frontend, DB migrations (Alembic).

---

## High-level architecture

```text
Telegram client
    → HTTPS POST /telegram/webhook (or /webhook/telegram)
        → optional secret: X-Telegram-Bot-Api-Secret-Token
        → if ALLOWED_TELEGRAM_IDS non-empty: chat_id must be listed; else short reply and return
        → MessageParser
            → fallback (/g, /i, /r) OR (if ENABLE_LLM_PARSER) OpenAI structured JSON
            → if LLM off and not fallback: LlmDisabledError → user-facing v1-only message
            → Pydantic validate_action → Action union
        → ActionService.execute → SQLite (SQLAlchemy)
        → TelegramClient.sendMessage

Background: APScheduler interval job → send_due_reminders → mark reminders sent
```

---

## Stack

| Layer | Choice |
|--------|--------|
| Runtime | Python 3 (async where needed) |
| HTTP / ASGI | **FastAPI** + **Uvicorn** |
| Config | **pydantic-settings**, `.env` |
| Database | **SQLite** via **SQLAlchemy 2** (Declarative, `future=True`) |
| Telegram | **httpx** (async) → `https://api.telegram.org/bot<token>/…` |
| LLM | **OpenAI** Python SDK, **chat.completions** + **JSON Schema** strict structured output |
| Jobs | **APScheduler** `AsyncIOScheduler`, interval by `REMINDER_CHECK_SECONDS` |
| Tests | **pytest** (`tests/`) |
| Deploy | Optional **Docker** image + `docker-compose` (`Dockerfile`, [`docker-compose.yml`](docker-compose.yml)); SQLite on persistent Docker/Coolify volume at **`/app/data`** (`DATA_DIR`), see [`readme.md`](readme.md) |

**Dependencies:** runtime image uses `requirements-prod.txt` (no `pytest`). Dev / local install may use `requirements.txt` including `pytest`.

---

## Repository layout

```text
telegramBot/
  app/
    __init__.py
    main.py          # FastAPI app, lifespan (logging, init_db, scheduler), routes
    config.py        # Settings (get_settings), DATA_DIR=/app/data for Docker volumes
    database.py      # Engine, SessionLocal, init_db, get_db dependency
    models.py        # SQLAlchemy models: Expense, Income, Reminder, Note
    schemas.py       # RawParsedMessage, per-intent Action models, validate_action()
    errors.py        # ParserError, LlmDisabledError
    telegram.py      # TelegramClient: send_message, set_webhook
    llm.py           # LLMService, SYSTEM_PROMPT, STRUCTURED_OUTPUT_SCHEMA, parse()
    parser.py        # MessageParser: fallback vs LLM + validation
    fallback.py      # /g /i /r parsing without OpenAI
    actions.py       # ActionService: DB writes + query replies
    scheduler.py     # create_scheduler, send_due_reminders
    utils.py         # timezone, money/date parsing & formatting
  tests/
    test_fallback.py
    test_parser_llm.py
  requirements.txt
  requirements-prod.txt
  Dockerfile
  docker-compose.yml
  .dockerignore
  .env.example
```

---

## HTTP API (FastAPI)

| Method | Path | Role |
|--------|------|------|
| GET / HEAD | `/health` | Liveness: `GET` returns `status`, `service`, `version`; `HEAD` returns **200** without body (uptime monitors). |
| POST | `/telegram/set-webhook` | Body: `{"url":"<https webhook url>"}`. Validates `X-Telegram-Bot-Api-Secret-Token` if `TELEGRAM_WEBHOOK_SECRET` is set. Calls Telegram `setWebhook` (optional `secret_token`). |
| POST | `/telegram/webhook` | Main Telegram update receiver (alias below). |
| POST | `/webhook/telegram` | Same handler as `/telegram/webhook`. |

**Webhook handler behavior**

- Ignores updates without `message` / `edited_message` or without text.
- If **`ALLOWED_TELEGRAM_IDS`** is non-empty and **`chat_id`** is not in the list: send a short “not allowed” message and return (no DB).
- **`/start`**, **`/help`**: fixed Spanish help text, no DB/LLM (only after passing allowlist).
- **`/get`**: read-only DB totals for the chat (**Ingresos** + **Egresos**, historic sums); skips parser/LLM.
- Otherwise: `MessageParser.parse_message` → `ActionService.execute` → `TelegramClient.send_message`.
- **`LlmDisabledError`**: user sees a message that only `/g`, `/i`, `/r` are accepted until LLM is enabled.
- **`ParserError`** (other): user sees *"No pude entenderlo. Probá con: /g 25000 comida"*.
- **Other exceptions**: *"Tuve un problema guardando eso. Probá de nuevo."*

**Application lifespan**

- `configure_logging`, `init_db()`, start **APScheduler**, store on `app.state.scheduler`; on shutdown `scheduler.shutdown(wait=False)`.

---

## Configuration (`app/config.py` / `.env`)

| Setting | Purpose |
|---------|---------|
| `APP_TIMEZONE` | `ZoneInfo` for “now”, reminders, date logic (default `America/Argentina/Buenos_Aires`) |
| `LOG_LEVEL` | Root logging level |
| `ENVIRONMENT` | Default `development`. `production` / `prod`: use **`DATABASE_URL`** only. Else: use **`DATABASE_URL_LOCAL`** when non-empty, otherwise **`DATABASE_URL`**. |
| `DATABASE_URL_LOCAL` | Dev override (ignored in production). Typical: `sqlite:///./assistant.db`. |
| `DATABASE_URL` | SQLAlchemy URL. **Docker / Coolify (production):** `sqlite:////app/data/assistant.db` + volume on **`/app/data`** (`DATA_DIR`). |
| `TELEGRAM_BOT_TOKEN` | Bot token; empty → send is no-op (warning log) |
| `TELEGRAM_WEBHOOK_SECRET` | If set, required on webhook/set-webhook via `X-Telegram-Bot-Api-Secret-Token` |
| `ALLOWED_TELEGRAM_IDS` | Comma-separated `chat_id` integers in `.env`. If non-empty, only those chats are allowed. If empty/unset, any chat may use the bot. |
| `ENABLE_LLM_PARSER` | If `true`, non-command messages use OpenAI. Default `false` (v1: commands only). |
| `OPENAI_API_KEY` | Required when `ENABLE_LLM_PARSER=true` |
| `OPENAI_MODEL` | Model id (default `gpt-5-mini`) |
| `REMINDER_CHECK_SECONDS` | APScheduler interval for due reminders (default `60`) |

---

## Data model (SQLite)

- **`expenses`**: `chat_id`, `amount`, `category`, `date`, `description`, `created_at`. Index `(chat_id, date)`.
- **`incomes`**: `chat_id`, `amount`, `source`, `date`, `description`, `created_at`. Index `(chat_id, date)`.
- **`reminders`**: `chat_id`, `remind_at`, `text`, `is_sent`, `sent_at`, `created_at`. Index `(is_sent, remind_at)`.
- **`notes`**: `chat_id`, `text`, `tags` (JSON list), `created_at`.

`chat_id` scopes all data per Telegram chat. No migrations: `Base.metadata.create_all` on startup.

---

## Parsing pipeline

### 1. Fallback (no OpenAI)

If the message starts with `/g `, `/i `, or `/r ` (case-insensitive after trim):

- **`/g`**: expense — amount (+ optional multipliers: luca, mil, palo, etc.), optional relative day (`hoy`, `ayer`, …), category + description.
- **`/i`**: income — same amount/date rules, source + description.
- **`/r`**: reminder — optional **trailing date** `D/M/Y` or `D/M/YY` at end of the line (year under 100 → 2000+year); **or** relative day (`mañana`, `hoy`, …); optional time (`10am`, `14:30`); reminder text; must be strictly in the future.

Implemented in `app/fallback.py`; tested in `tests/test_fallback.py`.

### 2. LLM structured output (v2.0, gated)

Only runs when **`ENABLE_LLM_PARSER`** is **`true`** in settings. If the flag is **false** and the message is not a fallback command, **`LlmDisabledError`** is raised (handled in `main.py`).

`LLMService.parse()` calls OpenAI with:

- **Strict JSON schema** (`STRUCTURED_OUTPUT_SCHEMA` in `llm.py`): fixed keys including `intent`, monetary fields, `query_type`, `period`, etc.
- **System prompt** (`SYSTEM_PROMPT`): Spanish instructions for intents, date/amount normalization, query types, periods.

Response is `json.loads`’d to a dict, then **`validate_action()`** in `schemas.py` builds a discriminated **Action**:

| Intent | Action type | Validation highlights |
|--------|----------------|------------------------|
| `expense` | `ExpenseAction` | Positive `amount`, `category`, `date` (default today) |
| `income` | `IncomeAction` | Positive `amount`, `source`, `date` |
| `reminder` | `ReminderAction` | ISO-ish `datetime` → naive local; **must be future** |
| `note` | `NoteAction` | `text`, optional `tags` (normalized lowercase) |
| `query` | `QueryAction` | `query_type` not `unknown`; default `period` by query type |
| `unknown` / missing | — | **ParserError** |

---

## Query types (`QueryAction`)

| `query_type` | Behavior |
|----------------|----------|
| `expenses_total` | Sum `Expense.amount` for `chat_id`, filtered by `period` |
| `incomes_total` | Sum `Income.amount` |
| `balance` | Sum incomes − sum expenses |
| `reminders_list` | Up to 10 pending reminders (`is_sent=False`, `remind_at >= now`), optional period window |
| `notes_search` | Up to 5 notes, optional `text` filter (`ILIKE`) |

**Periods** (`_date_range` in `actions.py`): `today`, `week` (week starts Monday), `current_month` / `month`, `all` (no date filter for money aggregates).

---

## Actions / side effects (`ActionService`)

- **Create** rows for expense, income, reminder, note; **commit** per operation.
- **Queries** return short Spanish strings (money formatted with `format_money`, dates with `format_datetime` / `format_date` in `utils.py`).

---

## Reminder scheduler (`scheduler.py`)

- **AsyncIOScheduler** in `app_timezone`.
- Job **`send_due_reminders`**: loads up to 25 reminders with `is_sent=False` and `remind_at <= now`, sends *"Recordatorio: …"*, sets `is_sent=True`, `sent_at=now`. Uses a **new `SessionLocal()`** context (not request-scoped `get_db`).

---

## Utilities (`utils.py`)

- **`local_now` / `to_naive_local`**: consistent local timezone handling for DB comparisons.
- **`parse_iso_date` / `parse_iso_datetime`**: LLM output → Python date/datetime.
- **`parse_decimal`**: amounts for fallback (commas/dots, currency noise).
- **`format_money` / `format_datetime`**: user-facing AR-style formatting.

---

## Security notes

- Optional **`ALLOWED_TELEGRAM_IDS`** restricts which Telegram chats can use the bot.
- Webhook and set-webhook can require **shared secret** header aligned with Telegram’s `secret_token` when registering the webhook.
- **Do not commit** real `.env` or tokens.

---

## Testing and quality checks

```bash
python -m pytest
python -m compileall app tests
```

---

## Related doc

- **`readme.md`**: environment setup, running the server, webhook registration, health check.
