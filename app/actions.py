from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Expense, Income, Note, Reminder
from app.schemas import Action, ExpenseAction, IncomeAction, NoteAction, QueryAction, ReminderAction
from app.utils import format_datetime, format_money, local_now, to_naive_local


class ActionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def format_lifetime_totals(self, chat_id: int) -> str:
        """Sum all incomes and expenses for chat (no period filter)."""
        ingresos = self._sum_money(chat_id, Income, "all")
        egresos = self._sum_money(chat_id, Expense, "all")
        return f"Ingresos: {format_money(ingresos)}\nEgresos: {format_money(egresos)}"

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
        expense = Expense(
            chat_id=chat_id,
            amount=action.amount,
            category=action.category,
            date=action.date,
            description=action.description,
        )
        self.db.add(expense)
        self.db.commit()
        return f"Listo, guardé {format_money(action.amount)} en {action.category}."

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
        return f"Listo, guardé ingreso de {format_money(action.amount)} por {action.source}."

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
            return self._list_reminders(chat_id, action.period)

        if action.query_type == "notes_search":
            return self._list_notes(chat_id, action.text)

        return "No pude responder esa consulta."

    def _sum_money(self, chat_id: int, model, period: str) -> Decimal:
        stmt = select(func.coalesce(func.sum(model.amount), 0)).where(model.chat_id == chat_id)
        date_range = _date_range(period, local_now(self.settings).date())
        if date_range:
            start, end = date_range
            stmt = stmt.where(model.date >= start, model.date < end)
        return Decimal(self.db.execute(stmt).scalar_one() or 0)

    def _list_reminders(self, chat_id: int, period: str) -> str:
        now = to_naive_local(local_now(self.settings), self.settings)
        stmt = (
            select(Reminder)
            .where(Reminder.chat_id == chat_id, Reminder.is_sent.is_(False), Reminder.remind_at >= now)
            .order_by(Reminder.remind_at.asc())
            .limit(10)
        )
        date_range = _date_range(period, now.date())
        if date_range:
            start, end = date_range
            stmt = stmt.where(Reminder.remind_at >= datetime.combine(start, datetime.min.time()))
            stmt = stmt.where(Reminder.remind_at < datetime.combine(end, datetime.min.time()))

        reminders = self.db.execute(stmt).scalars().all()
        if not reminders:
            return "No tenés recordatorios pendientes."

        lines = [f"- {format_datetime(item.remind_at)}: {item.text}" for item in reminders]
        return "Tus próximos recordatorios:\n" + "\n".join(lines)

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


def _date_range(period: str, today: date) -> tuple[date, date] | None:
    if period == "all":
        return None
    if period == "today":
        return today, today + timedelta(days=1)
    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=7)
    if period in {"current_month", "month"}:
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    return None
