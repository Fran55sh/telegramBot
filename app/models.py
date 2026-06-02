from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("chat_id", "kind", "slug", name="uq_categories_chat_kind_slug"),
        Index("ix_categories_kind_active", "kind", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    group_slug: Mapped[str | None] = mapped_column(String(80))
    group_label: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"
    __table_args__ = (Index("ix_expenses_chat_date", "chat_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Income(TimestampMixin, Base):
    __tablename__ = "incomes"
    __table_args__ = (Index("ix_incomes_chat_date", "chat_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="otros-ingresos")
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"
    __table_args__ = (Index("ix_reminders_due", "is_sent", "remind_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class Note(TimestampMixin, Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
