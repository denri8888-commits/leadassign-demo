"""Экспоненциальное затухание веса наблюдений."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Union

DateLike = Union[date, datetime, str]


def to_date(value: DateLike) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def days_old(event_date: DateLike, as_of: DateLike) -> float:
    return max(0.0, float((to_date(as_of) - to_date(event_date)).days))


def recency_weight(event_date: DateLike, as_of: DateLike, lambda_: float) -> float:
    """weight = exp(-lambda * days_old)."""
    if lambda_ < 0:
        raise ValueError("lambda must be >= 0")
    return math.exp(-lambda_ * days_old(event_date, as_of))
