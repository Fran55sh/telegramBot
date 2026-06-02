from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import ReminderCreate, ReminderOut, ReminderUpdate
from app.config import Settings, get_settings
from app.models import Reminder
from app.utils import local_now, to_naive_local

router = APIRouter(prefix="/reminders", tags=["reminders"])


def _reminder_out(reminder: Reminder) -> ReminderOut:
    return ReminderOut.model_validate(reminder)


@router.get("", response_model=list[ReminderOut])
def list_reminders(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    status: str = Query(default="pending", pattern="^(pending|sent|all)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ReminderOut]:
    stmt = select(Reminder).where(Reminder.chat_id == user.chat_id)
    if status == "pending":
        stmt = stmt.where(Reminder.is_sent.is_(False))
    elif status == "sent":
        stmt = stmt.where(Reminder.is_sent.is_(True))
    stmt = stmt.order_by(Reminder.remind_at.desc()).offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [_reminder_out(row) for row in rows]


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(
    payload: ReminderCreate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
) -> ReminderOut:
    now = to_naive_local(local_now(settings), settings)
    remind_at = payload.remind_at.replace(tzinfo=None) if payload.remind_at.tzinfo else payload.remind_at
    if remind_at <= now:
        raise HTTPException(status_code=400, detail="Reminder must be in the future")
    reminder = Reminder(
        chat_id=user.chat_id,
        text=payload.text.strip(),
        remind_at=remind_at,
        amount=payload.amount,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return _reminder_out(reminder)


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
) -> ReminderOut:
    reminder = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    data = payload.model_dump(exclude_unset=True)
    if "remind_at" in data and data["remind_at"] is not None:
        remind_at = data["remind_at"]
        remind_at = remind_at.replace(tzinfo=None) if remind_at.tzinfo else remind_at
        now = to_naive_local(local_now(settings), settings)
        if remind_at <= now and not data.get("is_sent"):
            raise HTTPException(status_code=400, detail="Reminder must be in the future")
        data["remind_at"] = remind_at
    for key, value in data.items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return _reminder_out(reminder)


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> None:
    reminder = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.chat_id == user.chat_id)
    ).scalar_one_or_none()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
