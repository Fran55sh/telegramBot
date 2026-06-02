from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.models import Expense
from app.services.categories import category_label, resolve_category_slug

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _expense_out(db: Session, chat_id: int, expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        category_label=category_label(db, chat_id, "expense", expense.category),
        date=expense.date,
        description=expense.description,
        created_at=expense.created_at,
    )


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ExpenseOut]:
    stmt = select(Expense).where(Expense.chat_id == user.chat_id)
    if date_from:
        stmt = stmt.where(Expense.date >= date_from)
    if date_to:
        stmt = stmt.where(Expense.date <= date_to)
    if category:
        stmt = stmt.where(Expense.category == category)
    if q:
        stmt = stmt.where(Expense.description.ilike(f"%{q}%"))
    stmt = stmt.order_by(Expense.date.desc(), Expense.id.desc()).offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [_expense_out(db, user.chat_id, row) for row in rows]


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> ExpenseOut:
    slug = resolve_category_slug(db, user.chat_id, "expense", payload.category)
    expense = Expense(
        chat_id=user.chat_id,
        amount=payload.amount,
        category=slug,
        date=payload.date,
        description=payload.description,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _expense_out(db, user.chat_id, expense)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> ExpenseOut:
    expense = db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] is not None:
        data["category"] = resolve_category_slug(db, user.chat_id, "expense", data["category"])
    for key, value in data.items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return _expense_out(db, user.chat_id, expense)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> None:
    expense = db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
