"""Валидация данных."""

from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_HISTORY = [
    "date",
    "manager",
    "region",
    "product",
    "sale",
    "sale_amount",
    "gm",
]

REQUIRED_APPLICATIONS = ["application_id", "date", "region", "product"]


class ValidationError(Exception):
    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


def validate_history(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    for col in REQUIRED_HISTORY:
        if col not in df.columns:
            errors.append(f"Отсутствует обязательная колонка истории: {col}")
    if errors:
        return errors
    if df["application_id"].duplicated().any() if "application_id" in df.columns else False:
        errors.append("Дубликаты application_id в истории")
    if (df["sale_amount"] < 0).any():
        errors.append("Отрицательная сумма продажи недопустима")
    if (df["gm"] < 0).any():
        errors.append("Отрицательная GM недопустима")
    if df["gm"].isna().any() or df["sale_amount"].isna().any():
        errors.append("Пустые значения в gm/sale_amount")
    if not df["sale"].isin([0, 1, True, False]).all():
        errors.append("Поле sale должно быть 0/1")
    return errors


def validate_applications(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    for col in REQUIRED_APPLICATIONS:
        if col not in df.columns:
            errors.append(f"Отсутствует обязательная колонка заявки: {col}")
    if errors:
        return errors
    if df["application_id"].duplicated().any():
        errors.append("Дубликаты ID заявок")
    if df[REQUIRED_APPLICATIONS].isna().any().any():
        errors.append("Критичные пустые значения в заявках")
    return errors


def validate_capacity(team_capacity: int, manager_capacities: dict[str, int], n_apps: int) -> list[str]:
    errors: list[str] = []
    if team_capacity <= 0:
        errors.append("capacity команды должна быть > 0")
    if team_capacity > n_apps:
        # не ошибка — просто часть capacity не будет использована; предупреждение
        pass
    for m, c in manager_capacities.items():
        if c < 0:
            errors.append(f"Capacity менеджера {m} не может быть отрицательной")
    return errors


def validate_settings(settings: Any, n_apps: int) -> list[str]:
    errors = validate_capacity(settings.team_capacity, settings.manager_capacities, n_apps)
    if settings.prior_strength < 0:
        errors.append("prior_strength должна быть >= 0")
    if settings.recency_lambda < 0:
        errors.append("recency_lambda должна быть >= 0")
    return errors
