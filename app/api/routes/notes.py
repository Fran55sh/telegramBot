from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import NoteCreate, NoteOut, NoteUpdate
from app.models import Note

router = APIRouter(prefix="/notes", tags=["notes"])


def _normalize_tags(tags: list[str]) -> list[str]:
    return [tag.strip().lower() for tag in tags if tag.strip()]


@router.get("", response_model=list[NoteOut])
def list_notes(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    q: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[NoteOut]:
    stmt = select(Note).where(Note.chat_id == user.chat_id)
    if q:
        stmt = stmt.where(Note.text.ilike(f"%{q}%"))
    stmt = stmt.order_by(Note.created_at.desc()).offset(offset).limit(limit)
    rows = db.execute(stmt).scalars().all()
    if tag:
        tag_lower = tag.strip().lower()
        rows = [row for row in rows if tag_lower in row.tags]
    return [NoteOut.model_validate(row) for row in rows]


@router.post("", response_model=NoteOut, status_code=201)
def create_note(
    payload: NoteCreate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> NoteOut:
    note = Note(chat_id=user.chat_id, text=payload.text.strip(), tags=_normalize_tags(payload.tags))
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note)


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> NoteOut:
    note = db.execute(select(Note).where(Note.id == note_id, Note.chat_id == user.chat_id)).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    data = payload.model_dump(exclude_unset=True)
    if "text" in data and data["text"] is not None:
        data["text"] = data["text"].strip()
    if "tags" in data and data["tags"] is not None:
        data["tags"] = _normalize_tags(data["tags"])
    for key, value in data.items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> None:
    note = db.execute(select(Note).where(Note.id == note_id, Note.chat_id == user.chat_id)).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
