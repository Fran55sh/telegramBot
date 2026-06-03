FROM node:20-bookworm-slim AS frontend-build
WORKDIR /frontend

ARG VITE_WEB_APP_TOKEN=dev-token-change-me
ARG VITE_TELEGRAM_CHAT_ID=
ENV VITE_WEB_APP_TOKEN=$VITE_WEB_APP_TOKEN
ENV VITE_TELEGRAM_CHAT_ID=$VITE_TELEGRAM_CHAT_ID

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY app ./app
COPY --from=frontend-build /frontend/dist ./frontend/dist

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh \
    && mkdir -p /app/data \
    && chown -R app:app /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
