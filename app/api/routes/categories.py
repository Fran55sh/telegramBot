from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import CategoryCreate, CategoryGroupOut, CategoryOut, CategoryUpdate
from app.services import categories as category_service

router = APIRouter(prefix="/categories", tags=["categories"])


def _to_group_out(groups) -> list[CategoryGroupOut]:
    return [
        CategoryGroupOut(
            slug=g.slug,
            label=g.label,
            categories=[CategoryOut.model_validate(c) for c in g.categories],
        )
        for g in groups
    ]


@router.get("", response_model=list[CategoryGroupOut])
def list_categories(
    kind: str,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> list[CategoryGroupOut]:
    if kind not in {"expense", "income"}:
        raise HTTPException(status_code=400, detail="kind must be expense or income")
    cats = category_service.list_categories(db, user.chat_id, kind)
    return _to_group_out(category_service.group_categories(cats))


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> CategoryOut:
    category = category_service.create_category(
        db,
        user.chat_id,
        kind=payload.kind,
        label=payload.label,
        group_label=payload.group_label,
        group_slug=payload.group_slug,
    )
    return CategoryOut.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> CategoryOut:
    category = category_service.update_category(
        db,
        user.chat_id,
        category_id,
        **payload.model_dump(exclude_unset=True),
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryOut.model_validate(category)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
) -> None:
    ok = category_service.deactivate_category(db, user.chat_id, category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
