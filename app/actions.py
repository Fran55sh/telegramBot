from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.expense_categories import normalize_expense_category, subcategory_display
from app.models import Expense, Income, Note, Reminder
from app.months import month_range, month_title, parse_month_arg
from app.periods import period_label, resolve_date_range
from app.schemas import Action, ExpenseAction, IncomeAction, NoteAction, QueryAction, ReminderAction
from app.utils import format_date, format_datetime, format_money, local_now, to_naive_local


class ActionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def format_monthly_report(self, chat_id: int, month_arg: str = "") -> str:
        today = local_now(self.settings).date()
        year, month = parse_month_arg(month_arg, today)
        start, end = month_range(year, month)
        title = month_title(year, month)

        incomes = self._list_incomes(chat_id, start, end)
        expenses = self._list_expenses(chat_id, start, end)

        if not incomes and not expenses:
            return f"No hay movimientos en {title}."

        total_in = sum((i.amount for i in incomes), Decimal(0))
        total_out = sum((e.amount for e in expenses), Decimal(0))

        by_category: dict[str, Decimal] = defaultdict(Decimal)
        for item in expenses:
            by_category[item.category] += item.amount

        lines = [title, "", f"Ingresos: {format_money(total_in)}", f"Egresos: {format_money(total_out)}"]

        for category, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            label = subcategory_display(category)
            pct = _expense_percent(amount, total_out)
            lines.append(f" - {label} {format_money(amount)} ({pct})")

        lines.append("")
        lines.append(f"Balance: {format_money(total_in - total_out)}")
        return "\n".join(lines)

    def execute(self, chat_id: int, action: Action) -> str:
        if isinstance(action, ExpenseAction):
            return self._create_expense(chat_id, action)
        if isinstance(action, IncomeAction):
            return self._create_income(chat_id, action)
        if isinstance(action, ReminderAction):
            return self._create_reminder(chat_id, action)
        if isinstance(action, NoteAction):
            return self._create_note(chat_id, action)
        if isinstance(action, QueryAction):
            return self._run_query(chat_id, action)
        raise ValueError("Unsupported action")

    def _create_expense(self, chat_id: int, action: ExpenseAction) -> str:
        category = normalize_expense_category(action.category)
        expense = Expense(
            chat_id=chat_id,
            amount=action.amount,
            category=category,
            date=action.date,
            description=action.description,
        )
        self.db.add(expense)
        self.db.commit()
        cat_label = subcategory_display(category)
        return (
            f"Listo, guardé {format_money(action.amount)} en {cat_label} "
            f"({format_date(action.date)})."
        )

    def _create_income(self, chat_id: int, action: IncomeAction) -> str:
        income = Income(
            chat_id=chat_id,
            amount=action.amount,
            source=action.source,
            date=action.date,
            description=action.description,
        )
        self.db.add(income)
        self.db.commit()
        return (
            f"Listo, guardé ingreso de {format_money(action.amount)} por {action.source} "
            f"({format_date(action.date)})."
        )

    def _create_reminder(self, chat_id: int, action: ReminderAction) -> str:
        reminder = Reminder(chat_id=chat_id, remind_at=action.datetime, text=action.text)
        self.db.add(reminder)
        self.db.commit()
        return f"Listo, te recuerdo el {format_datetime(action.datetime)}: {action.text}."

    def _create_note(self, chat_id: int, action: NoteAction) -> str:
        note = Note(chat_id=chat_id, text=action.text, tags=action.tags)
        self.db.add(note)
        self.db.commit()
        return "Listo, guardé la nota."

    def _run_query(self, chat_id: int, action: QueryAction) -> str:
        if action.query_type == "expenses_total":
            total = self._sum_money(chat_id, Expense, action.period)
            return f"Gastaste {format_money(total)} en el período."

        if action.query_type == "incomes_total":
            total = self._sum_money(chat_id, Income, action.period)
            return f"Recibiste {format_money(total)} en el período."

        if action.query_type == "balance":
            incomes = self._sum_money(chat_id, Income, action.period)
            expenses = self._sum_money(chat_id, Expense, action.period)
            return f"Balance: {format_money(incomes - expenses)}."

        if action.query_type == "reminders_list":
            return self._list_reminders(
                chat_id,
                action.period,
                date_from=action.date_from,
                date_to=action.date_to,
            )

        if action.query_type == "notes_search":
            return self._list_notes(chat_id, action.text)

        return "No pude responder esa consulta."

    def _list_incomes(self, chat_id: int, start: date, end: date) -> list[Income]:
        stmt = (
            select(Income)
            .where(Income.chat_id == chat_id, Income.date >= start, Income.date < end)
            .order_by(Income.date.asc(), Income.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def _list_expenses(self, chat_id: int, start: date, end: date) -> list[Expense]:
        stmt = (
            select(Expense)
            .where(Expense.chat_id == chat_id, Expense.date >= start, Expense.date < end)
            .order_by(Expense.date.asc(), Expense.id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def _sum_money(self, chat_id: int, model, period: str) -> Decimal:
        stmt = select(func.coalesce(func.sum(model.amount), 0)).where(model.chat_id == chat_id)
        date_range = resolve_date_range(period, local_now(self.settings).date())
        if date_range:
            start, end = date_range
            stmt = stmt.where(model.date >= start, model.date < end)
        return Decimal(self.db.execute(stmt).scalar_one() or 0)

    def _list_reminders(
        self,
        chat_id: int,
        period: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> str:
        now = to_naive_local(local_now(self.settings), self.settings)
        stmt = (
            select(Reminder)
            .where(Reminder.chat_id == chat_id, Reminder.is_sent.is_(False), Reminder.remind_at >= now)
            .order_by(Reminder.remind_at.asc())
            .limit(10)
        )
        date_range = resolve_date_range(
            period,
            now.date(),
            date_from=date_from,
            date_to=date_to,
        )
        if date_range:
            start, end = date_range
            stmt = stmt.where(Reminder.remind_at >= datetime.combine(start, datetime.min.time()))
            stmt = stmt.where(Reminder.remind_at < datetime.combine(end, datetime.min.time()))

        reminders = self.db.execute(stmt).scalars().all()
        label = period_label(period, date_from=date_from, date_to=date_to)
        if not reminders:
            if period == "all":
                return "No tenés recordatorios pendientes."
            return f"No tenés recordatorios pendientes para {label}."

        lines = [f"- {format_datetime(item.remind_at)}: {item.text}" for item in reminders]
        header = "Tus próximos recordatorios" if period == "all" else f"Recordatorios para {label}"
        return header + ":\n" + "\n".join(lines)

    def _list_notes(self, chat_id: int, search_text: str | None) -> str:
        stmt = select(Note).where(Note.chat_id == chat_id).order_by(Note.created_at.desc()).limit(5)
        if search_text:
            stmt = stmt.where(Note.text.ilike(f"%{search_text}%"))

        notes = self.db.execute(stmt).scalars().all()
        if not notes:
            return "No encontré notas."

        lines = []
        for note in notes:
            tags = f" ({', '.join(note.tags)})" if note.tags else ""
            lines.append(f"- {note.text}{tags}")
        return "Notas:\n" + "\n".join(lines)


def _expense_percent(category_total: Decimal, expenses_total: Decimal) -> str:
    if expenses_total <= 0:
        return "0%"
    pct = (category_total / expenses_total * 100).quantize(Decimal("0.1"))
    if pct == pct.to_integral_value():
        return f"{int(pct)}%"
    text = f"{pct:.1f}".replace(".", ",")
    return f"{text}%"
