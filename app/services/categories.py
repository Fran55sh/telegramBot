"""Persisted category catalog with seed defaults and per-user overrides."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.expense_categories import EXPENSE_GROUPS, SUBCATEGORY_LABELS
from app.models import Category

INCOME_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("ingresos-laborales", "Ingresos laborales", ("sueldo", "freelance", "bonificaciones")),
    ("ingresos-pasivos", "Ingresos pasivos", ("dividendos", "intereses", "alquileres")),
    ("ingresos-variables", "Ingresos variables", ("ventas", "extras", "reembolsos")),
    ("sin-clasificar-ingresos", "Sin clasificar", ("otros-ingresos",)),
)

INCOME_LABELS: dict[str, str] = {
    "sueldo": "sueldo",
    "freelance": "freelance",
    "bonificaciones": "bonificaciones",
    "dividendos": "dividendos",
    "intereses": "intereses",
    "alquileres": "alquileres",
    "ventas": "ventas",
    "extras": "extras",
    "reembolsos": "reembolsos",
    "otros-ingresos": "otros ingresos",
}


@dataclass(frozen=True)
class CategoryGroupView:
    slug: str
    label: str
    categories: tuple[Category, ...]


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = (
        lowered.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    compact = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return compact or "categoria"


def seed_default_categories(db: Session) -> None:
    existing = db.execute(select(Category.id).limit(1)).scalar_one_or_none()
    if existing is not None:
        return

    sort = 0
    for group in EXPENSE_GROUPS:
        for sub in group.subcategories:
            db.add(
                Category(
                    chat_id=None,
                    kind="expense",
                    slug=sub,
                    label=SUBCATEGORY_LABELS.get(sub, sub.replace("-", " ")),
                    group_slug=group.slug,
                    group_label=group.label,
                    is_active=True,
                    is_system=True,
                    sort_order=sort,
                )
            )
            sort += 1

    sort = 0
    for group_slug, group_label, subs in INCOME_GROUPS:
        for sub in subs:
            db.add(
                Category(
                    chat_id=None,
                    kind="income",
                    slug=sub,
                    label=INCOME_LABELS.get(sub, sub.replace("-", " ")),
                    group_slug=group_slug,
                    group_label=group_label,
                    is_active=True,
                    is_system=True,
                    sort_order=sort,
                )
            )
            sort += 1
    db.commit()


def list_categories(db: Session, chat_id: int, kind: str, *, include_inactive: bool = False) -> list[Category]:
    stmt = select(Category).where(
        Category.kind == kind,
        or_(Category.chat_id.is_(None), Category.chat_id == chat_id),
    )
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    stmt = stmt.order_by(Category.sort_order.asc(), Category.label.asc())
    rows = list(db.execute(stmt).scalars().all())
    return _dedupe_by_slug(rows)


def _dedupe_by_slug(categories: list[Category]) -> list[Category]:
    """User-specific category overrides global slug."""
    by_slug: dict[str, Category] = {}
    for cat in categories:
        current = by_slug.get(cat.slug)
        if current is None or (cat.chat_id is not None and current.chat_id is None):
            by_slug[cat.slug] = cat
    return list(by_slug.values())


def group_categories(categories: list[Category]) -> list[CategoryGroupView]:
    groups: dict[str, CategoryGroupView] = {}
    for cat in categories:
        gslug = cat.group_slug or "otros"
        glabel = cat.group_label or "Otros"
        if gslug not in groups:
            groups[gslug] = CategoryGroupView(slug=gslug, label=glabel, categories=())
        current = groups[gslug]
        groups[gslug] = CategoryGroupView(
            slug=current.slug,
            label=current.label,
            categories=current.categories + (cat,),
        )
    return sorted(groups.values(), key=lambda g: (g.categories[0].sort_order if g.categories else 0, g.label))


def resolve_category_slug(db: Session, chat_id: int, kind: str, raw: str) -> str:
    key = slugify(raw)
    categories = list_categories(db, chat_id, kind)
    slugs = {c.slug for c in categories}
    if key in slugs:
        return key
    for cat in categories:
        if slugify(cat.label) == key:
            return cat.slug
    fallback = "sin-clasificar" if kind == "expense" else "otros-ingresos"
    return fallback if fallback in slugs else (categories[0].slug if categories else fallback)


def category_label(db: Session, chat_id: int, kind: str, slug: str) -> str:
    stmt = select(Category).where(
        Category.kind == kind,
        Category.slug == slug,
        or_(Category.chat_id.is_(None), Category.chat_id == chat_id),
    )
    rows = list(db.execute(stmt).scalars().all())
    if not rows:
        return slug.replace("-", " ")
    rows.sort(key=lambda c: (0 if c.chat_id is not None else 1))
    return rows[0].label


def create_category(
    db: Session,
    chat_id: int,
    *,
    kind: str,
    label: str,
    group_label: str | None = None,
    group_slug: str | None = None,
) -> Category:
    base_slug = slugify(label)
    slug = base_slug
    suffix = 2
    while db.execute(
        select(Category.id).where(Category.chat_id == chat_id, Category.kind == kind, Category.slug == slug)
    ).scalar_one_or_none():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    category = Category(
        chat_id=chat_id,
        kind=kind,
        slug=slug,
        label=label.strip(),
        group_slug=group_slug or slugify(group_label or "Personalizado"),
        group_label=group_label or "Personalizado",
        is_active=True,
        is_system=False,
        sort_order=999,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, chat_id: int, category_id: int, **fields) -> Category | None:
    category = db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()
    if category is None:
        return None
    if category.chat_id not in (None, chat_id):
        return None
    if category.chat_id is None:
        fields = {k: v for k, v in fields.items() if k in {"label", "group_label", "sort_order"}}
    if category.is_system and fields.get("is_active") is False:
        fields.pop("is_active", None)
    for key, value in fields.items():
        if value is not None and hasattr(category, key):
            setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def deactivate_category(db: Session, chat_id: int, category_id: int) -> bool:
    category = db.execute(
        select(Category).where(Category.id == category_id, Category.chat_id == chat_id, Category.is_system.is_(False))
    ).scalar_one_or_none()
    if category is None:
        return False
    category.is_active = False
    db.commit()
    return True
