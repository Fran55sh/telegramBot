from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import IncomeCreate, IncomeOut, IncomeUpdate
from app.models import Income
from app.services.categories import category_label, resolve_category_slug

router = APIRouter(prefix="/incomes", tags=["incomes"])


def _income_out(db: Session, chat_id: int, income: Income) -> IncomeOut:
    return IncomeOut(
        id=income.id,
        amount=income.amount,
        category=income.category,
        category_label=category_label(db, chat_id, "income", income.category),
        source=income.source,
        date=income.date,
        description=income.description,
        created_at=income.created_at,
    )


@router.get("", response_model=list[IncomeOut])
def list_incomes(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[IncomeOut]:
    stmt = select(Income).where(Income.chat_id == user.chat_id)
    if date_from:
        stmt = stmt.where(Income.date >= date_from)
    if date_to:
        stmt = stmt.where(Income.date <= date_to)
    if category:
        stmt = stmt.where(Income.category == category)
    if q:
        stmt = stmt.where(
            or_(Income.description.ilike(f"%{q}%"), Income.source.ilike(f"%{q}%"))
        )
    stmt = stmt.order_by(Income.date.desc(), Income.id.desc()).offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [_income_out(db, user.chat_id, row) for row in rows]


@router.post("", response_model=IncomeOut, status_code=201)
def create_income(
    payload: IncomeCreate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> IncomeOut:
    slug = resolve_category_slug(db, user.chat_id, "income", payload.category)
    source = (payload.source or slug).strip().lower()
    income = Income(
        chat_id=user.chat_id,
        amount=payload.amount,
        category=slug,
        source=source,
        date=payload.date,
        description=payload.description,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return _income_out(db, user.chat_id, income)


@router.patch("/{income_id}", response_model=IncomeOut)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> IncomeOut:
    income = db.execute(
        select(Income).where(Income.id == income_id, Income.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if income is None:
        raise HTTPException(status_code=404, detail="Income not found")
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] is not None:
        data["category"] = resolve_category_slug(db, user.chat_id, "income", data["category"])
    if "source" in data and data["source"] is not None:
        data["source"] = data["source"].strip().lower()
    for key, value in data.items():
        setattr(income, key, value)
    db.commit()
    db.refresh(income)
    return _income_out(db, user.chat_id, income)


@router.delete("/{income_id}", status_code=204)
def delete_income(
    income_id: int,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> None:
    income = db.execute(
        select(Income).where(Income.id == income_id, Income.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if income is None:
        raise HTTPException(status_code=404, detail="Income not found")
    db.delete(income)
    db.commit()
