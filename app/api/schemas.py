from datetime import date as DateType, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    slug: str
    label: str
    group_slug: str | None
    group_label: str | None
    is_active: bool
    is_system: bool
    sort_order: int


class CategoryGroupOut(BaseModel):
    slug: str
    label: str
    categories: list[CategoryOut]


class CategoryCreate(BaseModel):
    kind: str = Field(pattern="^(expense|income)$")
    label: str = Field(min_length=1, max_length=120)
    group_label: str | None = Field(default=None, max_length=120)
    group_slug: str | None = Field(default=None, max_length=80)


class CategoryUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    group_label: str | None = Field(default=None, max_length=120)
    sort_order: int | None = None
    is_active: bool | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    category_label: str
    date: DateType
    description: str | None
    created_at: datetime


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category: str
    date: DateType
    description: str | None = None


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = None
    date: DateType | None = None
    description: str | None = None


class IncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    category_label: str
    source: str
    date: DateType
    description: str | None
    created_at: datetime


class IncomeCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category: str
    source: str | None = None
    date: DateType
    description: str | None = None


class IncomeUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = None
    source: str | None = None
    date: DateType | None = None
    description: str | None = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    remind_at: datetime
    amount: Decimal | None
    is_sent: bool
    sent_at: datetime | None
    created_at: datetime


class ReminderCreate(BaseModel):
    text: str = Field(min_length=1)
    remind_at: datetime
    amount: Decimal | None = Field(default=None, gt=0)


class ReminderUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    remind_at: datetime | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    is_sent: bool | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    tags: list[str]
    created_at: datetime


class NoteCreate(BaseModel):
    text: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None


class ActivityOut(BaseModel):
    id: int
    kind: str
    title: str
    subtitle: str
    amount: Decimal
    date: DateType
    created_at: datetime


class CategoryBreakdownOut(BaseModel):
    slug: str
    label: str
    amount: Decimal
    percent: float


class DashboardOut(BaseModel):
    balance: Decimal
    total_incomes: Decimal
    total_expenses: Decimal
    expenses_by_category: list[CategoryBreakdownOut]
    upcoming_reminders: list[ReminderOut]
    recent_activity: list[ActivityOut]
    pending_reminder_count: int


class MonthlyReportOut(BaseModel):
    year: int
    month: int
    total_incomes: Decimal
    total_expenses: Decimal
    balance: Decimal
    expenses_by_category: list[CategoryBreakdownOut]


class MeOut(BaseModel):
    chat_id: int
    display_name: str
    initials: str
    pending_reminder_count: int
