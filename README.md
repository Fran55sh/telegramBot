# Telegram Personal Assistant V1

Asistente personal simple por Telegram para registrar gastos, ingresos, recordatorios y notas usando lenguaje natural.

Flujo principal:

```text
Telegram message
-> FastAPI webhook
-> parse_message()
-> OpenAI structured output JSON
-> validacion Python
-> SQLite via SQLAlchemy
-> respuesta corta por Telegram
```

No usa LangChain, agentes, memoria conversacional, microservicios, Docker ni frontend.

## Stack

- Python
- FastAPI
- SQLite
- SQLAlchemy
- Telegram Bot API
- OpenAI API, modelo configurable (`gpt-5-mini` por defecto)
- APScheduler para enviar recordatorios

## Estructura

```text
app/
  actions.py      # ejecuta acciones sobre la DB y responde queries
  config.py       # settings centralizados desde .env
  database.py     # engine/session/init SQLite
  errors.py       # errores de parsing
  fallback.py     # comandos /g, /i, /r sin IA
  llm.py          # llamada OpenAI con structured outputs
  main.py         # FastAPI, health, webhook Telegram
  models.py       # modelos SQLAlchemy
  parser.py       # parse_message()
  scheduler.py    # job APScheduler para recordatorios
  schemas.py      # schemas Pydantic y validacion por intent
  telegram.py     # cliente Telegram Bot API
  utils.py        # fechas, importes, formatos
```

## Configuracion

1. Crear entorno e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Editar `.env`:

```env
APP_TIMEZONE=America/Argentina/Buenos_Aires
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./assistant.db

TELEGRAM_BOT_TOKEN=123456:telegram-token
TELEGRAM_WEBHOOK_SECRET=change-me

OPENAI_API_KEY=sk-proj-change-me
OPENAI_MODEL=gpt-5-mini

REMINDER_CHECK_SECONDS=60
```

## Correr local

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Verificacion

```bash
python -m pytest
python -m compileall app tests
```

## Configurar webhook de Telegram

Telegram necesita una URL publica HTTPS. Para desarrollo local podés usar ngrok, Cloudflare Tunnel o similar.

Ejemplo con ngrok:

```bash
ngrok http 8000
```

Luego registrar el webhook:

```bash
curl -X POST http://localhost:8000/telegram/set-webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: change-me" \
  -d '{"url":"https://TU-DOMINIO.ngrok-free.app/telegram/webhook"}'
```

El endpoint valida `TELEGRAM_WEBHOOK_SECRET` usando el header oficial
`X-Telegram-Bot-Api-Secret-Token` cuando el secreto esta configurado.

## Intenciones soportadas

### 1. expense

Ejemplos:

- `gasté 25000 en comida`
- `ayer compré tornillos por 12 lucas`

Campos finales:

```json
{
  "intent": "expense",
  "amount": 25000,
  "category": "comida",
  "date": "2026-05-09",
  "description": "gasté 25000 en comida"
}
```

### 2. income

Ejemplos:

- `recibí 1 millón de sueldo`
- `me pagaron 500 mil`

Campos finales:

```json
{
  "intent": "income",
  "amount": 1000000,
  "source": "sueldo",
  "date": "2026-05-09",
  "description": "recibí 1 millón de sueldo"
}
```

### 3. reminder

Ejemplos:

- `recordame el 20 de junio ir al dentista`
- `mañana tengo turno 10am`

Campos finales:

```json
{
  "intent": "reminder",
  "datetime": "2026-06-20T09:00:00",
  "text": "ir al dentista"
}
```

### 4. note

Ejemplos:

- `peli para ver matrix en hbo`
- `idea: importar fuentes slim`

Campos finales:

```json
{
  "intent": "note",
  "text": "peli para ver matrix en hbo",
  "tags": ["peli", "hbo"]
}
```

### 5. query

Ejemplos:

- `cuánto gasté este mes`
- `qué recordatorios tengo`

Query types internos:

- `expenses_total`
- `incomes_total`
- `balance`
- `reminders_list`
- `notes_search`

## Structured outputs

El LLM no ejecuta logica ni toca la base. Solo devuelve JSON con schema estricto.

Schema usado por `app/llm.py`:

```json
{
  "intent": "expense|income|reminder|note|query|unknown",
  "amount": 25000,
  "category": "comida",
  "source": null,
  "date": "2026-05-09",
  "description": "detalle util",
  "datetime": null,
  "text": null,
  "tags": null,
  "query_type": null,
  "period": null
}
```

Todos los campos son requeridos por el schema de OpenAI, pero los campos no usados van en `null`.
Despues, Pydantic valida condicionalmente segun `intent`.

## Prompt real

Resumen del system prompt incluido en `app/llm.py`:

```text
Sos un parser JSON para un asistente personal por Telegram.
No converses, no expliques y no ejecutes lógica: solo clasificá el mensaje y devolvé JSON válido.

Reglas:
- Usá fechas relativas contra el "ahora" provisto.
- Para expense/income, si no hay fecha explícita usá la fecha de hoy.
- Para reminder, devolvé datetime ISO 8601 local. Si falta hora, inferí 09:00.
- Normalizá importes: luca/lucas=1000, mil=1000, palo/palos=1000000, millón=1000000.
- query_type válido: expenses_total, incomes_total, balance, reminders_list, notes_search.
- period válido: today, week, current_month, month, all.
```

El user prompt agrega:

```text
Ahora local: 2026-05-09T11:30:00-03:00
Zona horaria: America/Argentina/Buenos_Aires
Mensaje de Telegram: ayer compré tornillos por 12 lucas
```

## Fallback sin IA

Si el mensaje empieza con estos comandos, no se llama a OpenAI:

- `/g` gasto
- `/i` ingreso
- `/r` recordatorio

Ejemplos:

```text
/g 25000 comida
/g 12 lucas tornillos
/i 1000000 sueldo
/i 500 mil freelance
/r mañana dentista
/r mañana 10am dentista
```

El fallback soporta importes basicos como `lucas`, `mil`, `palo` y fechas relativas simples como `hoy`, `ayer`, `mañana`, `pasado mañana`.

## Respuestas

Respuestas cortas y amigables:

- `Listo, guardé $25.000 en comida.`
- `Listo, guardé ingreso de $1.000.000 por sueldo.`
- `Listo, te recuerdo el 20/06/2026 09:00: ir al dentista.`
- `Gastaste $37.000 en el período.`

## Logs y errores

La app registra:

- update de Telegram recibido
- texto recibido
- request/response del LLM
- structured output invalido
- respuesta enviada al usuario
- envios de recordatorios

Si el LLM devuelve JSON invalido, faltan campos o la validacion falla, el usuario recibe una respuesta corta:

```text
No pude entenderlo. Probá con: /g 25000 comida
```

## Base de datos

SQLite se crea automaticamente en `assistant.db`.

Tablas:

- `expenses`
- `incomes`
- `reminders`
- `notes`

No hay migraciones en esta V1 para mantenerla simple. Si se extiende para produccion, el siguiente paso natural seria Alembic.
