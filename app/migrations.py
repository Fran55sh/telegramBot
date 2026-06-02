"""Idempotent SQLite schema upgrades for existing databases."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _column_names(engine: Engine, table: str) -> set[str]:
    return {col["name"] for col in inspect(engine).get_columns(table)}


def run_migrations(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        logger.info("Skipping SQLite-only migrations for dialect=%s", engine.dialect.name)
        return

    with engine.begin() as conn:
        income_cols = _column_names(engine, "incomes") if inspect(engine).has_table("incomes") else set()
        if income_cols and "category" not in income_cols:
            conn.execute(text("ALTER TABLE incomes ADD COLUMN category VARCHAR(80) DEFAULT 'otros-ingresos'"))
            conn.execute(text("UPDATE incomes SET category = source WHERE category IS NULL OR category = ''"))
            logger.info("Added incomes.category column")

        reminder_cols = _column_names(engine, "reminders") if inspect(engine).has_table("reminders") else set()
        if reminder_cols and "amount" not in reminder_cols:
            conn.execute(text("ALTER TABLE reminders ADD COLUMN amount NUMERIC(12, 2)"))
            logger.info("Added reminders.amount column")
