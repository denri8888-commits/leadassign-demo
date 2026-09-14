"""Загрузка и маппинг CSV/Excel."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from data.validation import validate_applications, validate_history


COLUMN_ALIASES = {
    "date": ["date", "дата", "deal_date"],
    "manager": ["manager", "менеджер", "manager_name"],
    "region": ["region", "регион"],
    "product": ["product", "продукт", "товар", "category"],
    "sale": ["sale", "продажа", "is_sale", "sold"],
    "sale_amount": ["sale_amount", "сумма", "amount", "revenue", "чек"],
    "gm": ["gm", "маржа", "gross_margin", "валовая_маржа"],
    "discount": ["discount", "скидка"],
    "application_id": ["application_id", "id", "заявка", "lead_id"],
    "negotiations_held": ["negotiations_held", "переговоры", "talk"],
}


def suggest_mapping(columns: list[str]) -> dict[str, str | None]:
    lower = {c: c for c in columns}
    lower_map = {c.lower().strip(): c for c in columns}
    mapping: dict[str, str | None] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        found = None
        for a in aliases:
            if a.lower() in lower_map:
                found = lower_map[a.lower()]
                break
        mapping[canonical] = found
    return mapping


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    rename = {src: dst for dst, src in mapping.items() if src and src in df.columns}
    out = df.rename(columns=rename).copy()
    return out


def read_table(content: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    bio = io.BytesIO(content)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(bio)
    return pd.read_csv(bio)


def preview_import(content: bytes, filename: str, kind: str = "history") -> dict[str, Any]:
    df = read_table(content, filename)
    mapping = suggest_mapping(list(df.columns))
    return {
        "filename": filename,
        "kind": kind,
        "columns": list(df.columns),
        "suggested_mapping": mapping,
        "preview_rows": df.head(8).fillna("").astype(str).to_dict(orient="records"),
        "row_count": len(df),
        "helpers": {
            "mapping": "Сопоставьте колонки файла с полями системы. Обязательные поля зависят от типа загрузки.",
            "preview": "Первые строки файла после чтения. Проверьте, что даты и суммы распознаны корректно.",
        },
    }


def apply_import(
    content: bytes,
    filename: str,
    kind: str,
    mapping: dict[str, str],
) -> tuple[pd.DataFrame, list[str]]:
    df = read_table(content, filename)
    mapped = apply_mapping(df, mapping)
    if kind == "history":
        # sale может быть строкой
        if "sale" in mapped.columns:
            mapped["sale"] = mapped["sale"].map(
                lambda x: 1 if str(x).lower() in ("1", "true", "yes", "да", "y") else (0 if str(x).lower() in ("0", "false", "no", "нет", "n") else x)
            )
            mapped["sale"] = pd.to_numeric(mapped["sale"], errors="coerce").fillna(0).astype(int)
        for col in ("sale_amount", "gm", "discount"):
            if col in mapped.columns:
                mapped[col] = pd.to_numeric(mapped[col], errors="coerce").fillna(0)
        errors = validate_history(mapped)
    else:
        errors = validate_applications(mapped)
    return mapped, errors
