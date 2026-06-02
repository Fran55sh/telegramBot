import os
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.migrations import run_migrations
from app.services.categories import seed_default_categories


@pytest.fixture()
async def client(monkeypatch):
    monkeypatch.setenv("WEB_APP_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    seed_default_categories(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client, db
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def auth_headers(chat_id: int = 42) -> dict[str, str]:
    return {
        "Authorization": "Bearer test-token",
        "X-Telegram-Chat-Id": str(chat_id),
    }


@pytest.mark.asyncio
async def test_me_and_categories(client):
    c, _db = client
    me = await c.get("/api/me", headers=auth_headers())
    assert me.status_code == 200
    assert me.json()["chat_id"] == 42

    cats = await c.get("/api/categories?kind=expense", headers=auth_headers())
    assert cats.status_code == 200
    groups = cats.json()
    assert len(groups) > 0
    assert any(g["categories"] for g in groups)


@pytest.mark.asyncio
async def test_expense_income_reminder_note_crud(client):
    c, _db = client
    headers = auth_headers()

    expense = await c.post(
        "/api/expenses",
        headers=headers,
        json={"amount": "25000.00", "category": "supermercado", "date": str(date.today()), "description": "Compras"},
    )
    assert expense.status_code == 201
    expense_id = expense.json()["id"]

    income = await c.post(
        "/api/incomes",
        headers=headers,
        json={
            "amount": "150000.00",
            "category": "sueldo",
            "source": "sueldo",
            "date": str(date.today()),
            "description": "Mes",
        },
    )
    assert income.status_code == 201

    remind_at = (datetime.utcnow() + timedelta(days=1)).replace(microsecond=0).isoformat()
    reminder = await c.post(
        "/api/reminders",
        headers=headers,
        json={"text": "Pagar luz", "remind_at": remind_at, "amount": "4500.00"},
    )
    assert reminder.status_code == 201
    assert reminder.json()["amount"] == "4500.00"

    note = await c.post(
        "/api/notes",
        headers=headers,
        json={"text": "Idea de ahorro", "tags": ["finanzas"]},
    )
    assert note.status_code == 201

    dashboard = await c.get("/api/reports/dashboard", headers=headers)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert Decimal(body["total_expenses"]) >= Decimal("25000")
    assert Decimal(body["total_incomes"]) >= Decimal("150000")
    assert len(body["recent_activity"]) >= 2

    deleted = await c.delete(f"/api/expenses/{expense_id}", headers=headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_create_custom_category(client):
    c, _db = client
    headers = auth_headers()
    created = await c.post(
        "/api/categories",
        headers=headers,
        json={"kind": "expense", "label": "Mascotas", "group_label": "Hogar"},
    )
    assert created.status_code == 201
    assert created.json()["label"] == "Mascotas"


@pytest.mark.asyncio
async def test_api_requires_auth(client):
    c, _db = client
    resp = await c.get("/api/me")
    assert resp.status_code == 401
