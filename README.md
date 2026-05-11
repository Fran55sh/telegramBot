# Telegram Personal Assistant — Setup and run

Minimal personal assistant bot over Telegram (expenses, incomes, reminders, notes, queries). Backend details and architecture are in **`system.md`**.

## Prerequisites

- **Python 3.10+** (3.11+ recommended)
- A **Telegram bot token** from [@BotFather](https://t.me/BotFather)
- **Optional:** `OPENAI_API_KEY` only if `ENABLE_LLM_PARSER=true` (natural language / v2.0)
- **Public HTTPS URL** for Telegram webhooks in production (or a tunnel such as ngrok / Cloudflare Tunnel for local dev)

## 1. Clone and virtual environment

```bash
cd telegramBot
python -m venv .venv
```

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Environment variables

Copy the example file and edit values:

```bash
copy .env.example .env
```

On Linux/macOS: `cp .env.example .env`

Fill at least:

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes (for real sends) | Token from BotFather |
| `OPENAI_API_KEY` | If `ENABLE_LLM_PARSER=true` | OpenAI API key for natural language |
| `ENABLE_LLM_PARSER` | Optional | Default `false`: only `/g`, `/i`, `/r` are accepted. Set `true` for free-text parsing (v2.0). |
| `ALLOWED_TELEGRAM_IDS` | Optional | Comma-separated Telegram `chat_id` values. If non-empty, only those chats can use the bot (private chat id is usually the same as the user id). Leave unset or empty to allow any user (e.g. local dev). |
| `TELEGRAM_WEBHOOK_SECRET` | Recommended in production | Random secret; must match header when calling webhook endpoints |
| `ENVIRONMENT` | Optional | Default `development`. In **production** use `production` or `prod`: the app uses **`DATABASE_URL`** only. In **development** (`development` / `dev` / `local`), **`DATABASE_URL_LOCAL`** overrides **`DATABASE_URL`** when set. |
| `DATABASE_URL` | Production required | Docker/Coolify: `sqlite:////app/data/assistant.db` with volume on **`/app/data`** (see **`DATA_DIR`** in [`app/config.py`](app/config.py)). Fallback in dev if `DATABASE_URL_LOCAL` is empty. |
| `DATABASE_URL_LOCAL` | Optional | **`ENVIRONMENT` not production:** local SQLite (e.g. `sqlite:///./assistant.db`). Ignored when `ENVIRONMENT` is production. |
| `APP_TIMEZONE` | Optional | Default `America/Argentina/Buenos_Aires` |
| `OPENAI_MODEL` | Optional | Default `gpt-5-mini` |
| `REMINDER_CHECK_SECONDS` | Optional | Reminder poll interval (seconds), default `60` |

See **`.env.example`** for the full list.

### Obtener el `chat_id` (para `ALLOWED_TELEGRAM_IDS`)

En un chat privado con el bot, el `chat.id` suele ser tu id de usuario. Podés verlo en los logs del servidor cuando mandás un mensaje (`telegram_message chat_id=...`), o usando un bot de información de usuario en Telegram.

## 3. Start the application

From the project root (with `.venv` activated):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Windows** note: if `uvicorn` is not on PATH, use:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API title: **Telegram Personal Assistant** (FastAPI)
- SQLite file is created automatically on first run (`assistant.db` by default)

## 4. Verify it is running

```bash
curl http://localhost:8000/health
```

Expected: JSON like `{"status":"ok","service":"Telegram Personal Assistant","version":"0.1.0"}`. `HEAD /health` returns **200** (no body), útil para monitores ligeros.

## 5. Point Telegram at your server (webhook)

Telegram only accepts **HTTPS** webhook URLs. For local development, expose port 8000 with a tunnel and register the webhook.

**Example: ngrok**

```bash
ngrok http 8000
```

Use the HTTPS URL ngrok gives you, then register the webhook (replace placeholders):

```bash
curl -X POST http://localhost:8000/telegram/set-webhook ^
  -H "Content-Type: application/json" ^
  -H "X-Telegram-Bot-Api-Secret-Token: YOUR_TELEGRAM_WEBHOOK_SECRET" ^
  -d "{\"url\":\"https://YOUR-SUBDOMAIN.ngrok-free.app/telegram/webhook\"}"
```

On Linux/macOS use `\` line continuation instead of `^`.

If `TELEGRAM_WEBHOOK_SECRET` is empty in `.env`, you can omit the header (not recommended for production).

The same payload can target either webhook path: **`/telegram/webhook`** or **`/webhook/telegram`**.

## 6. Quick test commands in Telegram

- `/get` — totales históricos: **Ingresos** y **Egresos** (sumas de ese chat)
- `/g 25000 comida` — expense (gasto)
- `/i 500000 sueldo` or `/I 500000 sueldo` — income (ingreso); command is case-insensitive
- `/r turno dni 25/6/26` — reminder on that date (day/month/year or 2-digit year); optional time: `/r mañana 10am dentista`
- Free-text Spanish, e.g. *"gasté 5000 en transporte"* — only if `ENABLE_LLM_PARSER=true` and `OPENAI_API_KEY` is set (v2.0)

## 7. Tests

```bash
python -m pytest
python -m compileall app tests
```

## 8. Docker (local or Coolify / Hetzner)

Production dependencies: **`requirements-prod.txt`** (same as `requirements.txt` without `pytest`). The image runs **Uvicorn** on port **8000** as a non-root user and exposes **`GET /health`** for health checks.

### Build and run with Compose

From the project root, create **`.env`** from **`.env.example`** and set secrets (Compose references **`env_file: .env`**).

```bash
docker compose build
docker compose up -d
```

- **Container name:** **`telegram_finance_bot`** (see [`docker-compose.yml`](docker-compose.yml)).
- **SQLite persistence:** Named Docker volume mounted at **`/app/data`**. Compose sets **`DATABASE_URL=sqlite:////app/data/assistant.db`**. In Coolify, set the same **`DATABASE_URL`** and mount persistent storage at **`/app/data`**.

### Coolify (summary)

1. Connect the Git repository and deploy with **Dockerfile** (build context: repo root) **or** with **Docker Compose** if you want the fixed `container_name` and volume in version control.
2. Expose container port **8000** behind your HTTPS domain (Coolify / Traefik).
3. In **Environment**: **`DATABASE_URL=sqlite:////app/data/assistant.db`**, **`TELEGRAM_BOT_TOKEN`**, optional vars from [`.env.example`](.env.example). **`ENVIRONMENT=production`** is defaulted in **`Dockerfile`** — do **not** set **`ENVIRONMENT=development`** in Coolify. **Unset / omit `DATABASE_URL_LOCAL`**; if present (e.g. copied laptop `.env`) with **`development`**, SQLite uses **`sqlite:///./assistant.db`** → file under **`/app/`** instead of **`/app/data/`**, so the mounted DB stays **empty**.
4. Mount **persistent storage** at **`/app/data`** so `assistant.db` survives redeploys.
5. Register Telegram’s webhook to `https://<your-domain>/telegram/webhook` via **`POST /telegram/set-webhook`** (same flow as in section 5).

If the platform injects a different **`PORT`**, map public traffic to container port **8000** in the UI, or override the start command to pass `--port` to match.

---

For intents, JSON schema, module map, and Docker deployment notes, see **`system.md`**.
