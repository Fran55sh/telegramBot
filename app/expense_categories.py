"""Expense category catalog: groups, subcategories, normalization and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.utils import format_money


@dataclass(frozen=True)
class ExpenseGroup:
    slug: str
    label: str
    subcategories: tuple[str, ...]


EXPENSE_GROUPS: tuple[ExpenseGroup, ...] = (
    ExpenseGroup("hogar", "🏠 Hogar", ("supermercado", "limpieza", "mantenimiento-casa", "muebles-electrodomesticos")),
    ExpenseGroup("comidas", "🍔 Comidas", ("restaurantes", "delivery", "salidas", "cafeteria")),
    ExpenseGroup("movilidad", "🚗 Movilidad", ("combustible", "transporte", "peajes", "mantenimiento-vehiculo")),
    ExpenseGroup("familia", "👨‍👩‍👧‍👦 Familia", ("hijos", "colegio", "gastos-familiares-varios")),
    ExpenseGroup("servicios", "⚡ Servicios", ("luz", "gas", "internet", "celular", "impuestos")),
    ExpenseGroup(
        "trabajo",
        "💻 Trabajo / Negocio",
        ("insumos-negocio", "herramientas", "software", "importaciones", "inversiones-negocio"),
    ),
    ExpenseGroup("personal", "🎮 Personal / Ocio", ("juegos", "tecnologia", "hobbies", "gustos")),
    ExpenseGroup("salud", "❤️ Salud", ("farmacia", "medicos", "estudios", "gimnasio")),
    ExpenseGroup("finanzas", "💰 Finanzas", ("prestamos", "intereses", "comisiones", "ahorro", "inversion")),
    ExpenseGroup("compras", "📦 Compras generales", ("compras-generales",)),
    ExpenseGroup("sin-clasificar", "❓ Sin clasificar", ("sin-clasificar",)),
)

SUBCATEGORY_LABELS: dict[str, str] = {
    "supermercado": "supermercado",
    "limpieza": "limpieza",
    "mantenimiento-casa": "mantenimiento casa",
    "muebles-electrodomesticos": "muebles/electrodomésticos",
    "restaurantes": "restaurantes",
    "delivery": "delivery",
    "salidas": "salidas",
    "cafeteria": "cafetería",
    "combustible": "combustible",
    "transporte": "transporte",
    "peajes": "peajes",
    "mantenimiento-vehiculo": "mantenimiento vehículo",
    "hijos": "hijos",
    "colegio": "colegio",
    "gastos-familiares-varios": "gastos familiares varios",
    "luz": "luz",
    "gas": "gas",
    "internet": "internet",
    "celular": "celular",
    "impuestos": "impuestos",
    "insumos-negocio": "insumos negocio",
    "herramientas": "herramientas",
    "software": "software",
    "importaciones": "importaciones",
    "inversiones-negocio": "inversiones negocio",
    "juegos": "juegos",
    "tecnologia": "tecnología",
    "hobbies": "hobbies",
    "gustos": "gustos",
    "farmacia": "farmacia",
    "medicos": "médicos",
    "estudios": "estudios",
    "gimnasio": "gimnasio",
    "prestamos": "préstamos",
    "intereses": "intereses",
    "comisiones": "comisiones",
    "ahorro": "ahorro",
    "inversion": "inversión",
    "compras-generales": "compras generales",
    "sin-clasificar": "sin clasificar",
}

_CATEGORY_ALIASES: dict[str, str] = {}
_GROUP_BY_SUB: dict[str, str] = {}


def _normalize_key(value: str) -> str:
    lowered = value.strip().lower()
    return (
        lowered.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace("_", " ")
        .replace("/", " ")
    )


def _register_alias(alias: str, subcategory: str) -> None:
    key = _normalize_key(alias)
    if key:
        _CATEGORY_ALIASES[key] = subcategory


for _group in EXPENSE_GROUPS:
    for _sub in _group.subcategories:
        _GROUP_BY_SUB[_sub] = _group.slug
        _register_alias(_sub, _sub)
        _register_alias(SUBCATEGORY_LABELS[_sub], _sub)

_register_alias("super", "supermercado")
_register_alias("nafta", "combustible")
_register_alias("uber", "transporte")
_register_alias("taxi", "transporte")
_register_alias("sube", "transporte")
_register_alias("wifi", "internet")
_register_alias("telefono", "celular")
_register_alias("telefono movil", "celular")
_register_alias("medico", "medicos")
_register_alias("doctor", "medicos")
_register_alias("comida", "restaurantes")


def normalize_expense_category(raw: str) -> str:
    key = _normalize_key(raw)
    if not key:
        return "sin-clasificar"
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    compact = key.replace(" ", "-")
    if compact in _GROUP_BY_SUB:
        return compact
    return "sin-clasificar"


def group_for_subcategory(subcategory: str) -> str:
    return _GROUP_BY_SUB.get(subcategory, "sin-clasificar")


def subcategory_display(subcategory: str) -> str:
    return SUBCATEGORY_LABELS.get(subcategory, subcategory.replace("-", " "))


def parse_category_from_text(text: str) -> tuple[str, str | None]:
    """Longest alias match at start; returns (subcategory_slug, optional description)."""
    normalized_text = _normalize_key(text)
    if not normalized_text:
        raise ValueError("empty text")

    best_sub: str | None = None
    best_alias: str | None = None
    best_len = 0
    for alias, sub in _CATEGORY_ALIASES.items():
        if normalized_text == alias or normalized_text.startswith(f"{alias} "):
            if len(alias) > best_len:
                best_len = len(alias)
                best_sub = sub
                best_alias = alias

    if best_sub is None:
        words = text.split()
        return normalize_expense_category(words[0]), (" ".join(words[1:]).strip() or None)

    alias_words = len(best_alias.split())
    desc = " ".join(text.split()[alias_words:]).strip()
    return best_sub, desc or None


def format_expense_groups_report(grouped: dict[str, dict[str, Decimal]]) -> list[str]:
    lines: list[str] = []
    for group in EXPENSE_GROUPS:
        sub_totals = grouped.get(group.slug)
        if not sub_totals:
            continue
        group_total = sum(sub_totals.values())
        lines.append(f"{group.label} — {format_money(group_total)}")
        for sub in group.subcategories:
            amount = sub_totals.get(sub)
            if amount and amount > 0:
                lines.append(f"  {subcategory_display(sub)}: {format_money(amount)}")
        for sub, amount in sub_totals.items():
            if sub not in group.subcategories and amount > 0:
                lines.append(f"  {subcategory_display(sub)}: {format_money(amount)}")
    return lines
