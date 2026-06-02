"""Shared finance reporting helpers for API and Telegram."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Expense, Income, Reminder
from app.months import month_range
from app.services.categories import category_label
from app.utils import local_now, to_naive_local


@dataclass(frozen=True)
class CategoryBreakdown:
    slug: str
    label: str
    amount: Decimal
    percent: float


@dataclass(frozen=True)
class ActivityItem:
    id: int
    kind: str
    title: str
    subtitle: str
    amount: Decimal
    date: date
    created_at: datetime


def sum_expenses(db: Session, chat_id: int, start: date, end: date) -> Decimal:
    stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.chat_id == chat_id,
        Expense.date >= start,
        Expense.date < end,
    )
    return Decimal(db.execute(stmt).scalar_one() or 0)


def sum_incomes(db: Session, chat_id: int, start: date, end: date) -> Decimal:
    stmt = select(func.coalesce(func.sum(Income.amount), 0)).where(
        Income.chat_id == chat_id,
        Income.date >= start,
        Income.date < end,
    )
    return Decimal(db.execute(stmt).scalar_one() or 0)


def expense_breakdown(db: Session, chat_id: int, start: date, end: date) -> list[CategoryBreakdown]:
    stmt = (
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.chat_id == chat_id, Expense.date >= start, Expense.date < end)
        .group_by(Expense.category)
    )
    rows = db.execute(stmt).all()
    total = sum((Decimal(amount) for _, amount in rows), Decimal(0))
    items: list[CategoryBreakdown] = []
    for slug, amount in rows:
        dec = Decimal(amount or 0)
        pct = float((dec / total * 100).quantize(Decimal("0.1"))) if total > 0 else 0.0
        items.append(
            CategoryBreakdown(
                slug=slug,
                label=category_label(db, chat_id, "expense", slug),
                amount=dec,
                percent=pct,
            )
        )
    return sorted(items, key=lambda x: x.amount, reverse=True)


def recent_activity(db: Session, chat_id: int, *, limit: int = 10) -> list[ActivityItem]:
    expenses = db.execute(
        select(Expense).where(Expense.chat_id == chat_id).order_by(Expense.date.desc(), Expense.id.desc()).limit(limit)
    ).scalars().all()
    incomes = db.execute(
        select(Income).where(Income.chat_id == chat_id).order_by(Income.date.desc(), Income.id.desc()).limit(limit)
    ).scalars().all()

    items: list[ActivityItem] = []
    for e in expenses:
        items.append(
            ActivityItem(
                id=e.id,
                kind="expense",
                title=e.description or category_label(db, chat_id, "expense", e.category),
                subtitle=category_label(db, chat_id, "expense", e.category),
                amount=-e.amount,
                date=e.date,
                created_at=e.created_at,
            )
        )
    for i in incomes:
        items.append(
            ActivityItem(
                id=i.id,
                kind="income",
                title=i.description or category_label(db, chat_id, "income", i.category),
                subtitle=category_label(db, chat_id, "income", i.category),
                amount=i.amount,
                date=i.date,
                created_at=i.created_at,
            )
        )
    items.sort(key=lambda x: (x.date, x.created_at), reverse=True)
    return items[:limit]


def upcoming_reminders(db: Session, settings: Settings, chat_id: int, *, limit: int = 5) -> list[Reminder]:
    now = to_naive_local(local_now(settings), settings)
    stmt = (
        select(Reminder)
        .where(Reminder.chat_id == chat_id, Reminder.is_sent.is_(False), Reminder.remind_at >= now)
        .order_by(Reminder.remind_at.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def pending_reminder_count(db: Session, settings: Settings, chat_id: int) -> int:
    now = to_naive_local(local_now(settings), settings)
    stmt = select(func.count()).select_from(Reminder).where(
        Reminder.chat_id == chat_id,
        Reminder.is_sent.is_(False),
        Reminder.remind_at >= now,
    )
    return int(db.execute(stmt).scalar_one() or 0)


def monthly_report(db: Session, chat_id: int, year: int, month: int) -> dict:
    start, end = month_range(year, month)
    total_in = sum_incomes(db, chat_id, start, end)
    total_out = sum_expenses(db, chat_id, start, end)
    breakdown = expense_breakdown(db, chat_id, start, end)
    return {
        "year": year,
        "month": month,
        "total_incomes": total_in,
        "total_expenses": total_out,
        "balance": total_in - total_out,
        "expenses_by_category": breakdown,
    }


def dashboard_summary(db: Session, settings: Settings, chat_id: int) -> dict:
    today = local_now(settings).date()
    start, end = month_range(today.year, today.month)
    total_in = sum_incomes(db, chat_id, start, end)
    total_out = sum_expenses(db, chat_id, start, end)
    return {
        "balance": total_in - total_out,
        "total_incomes": total_in,
        "total_expenses": total_out,
        "expenses_by_category": expense_breakdown(db, chat_id, start, end),
        "upcoming_reminders": upcoming_reminders(db, settings, chat_id),
        "recent_activity": recent_activity(db, chat_id),
        "pending_reminder_count": pending_reminder_count(db, settings, chat_id),
    }
