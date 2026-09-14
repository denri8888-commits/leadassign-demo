"""Текущая форма менеджера: короткое окно vs длинная база."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import pandas as pd

from analytics.recency import to_date


@dataclass
class ManagerForm:
    manager: str
    recent_metric: float
    previous_metric: float
    change_pct: float | None
    direction: str  # up | down | flat | unknown
    recent_n: int
    previous_n: int
    metric_name: str
    low_sample: bool
    comment: str
    short_metric: float = 0.0
    long_metric: float = 0.0
    short_n: int = 0
    long_n: int = 0
    dip_flag: bool = False
    short_days: int = 14
    long_days: int = 180


def _gm_per_negotiation(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    talks = len(df)
    if talks == 0:
        return 0.0
    gm_sum = float(df.loc[df["sale"] == 1, "gm"].fillna(0).sum())
    return gm_sum / talks


def compute_manager_form(
    history: pd.DataFrame,
    manager: str,
    as_of,
    recent_days: int = 30,
    previous_days: int = 30,
    min_observations: int = 5,
    short_days: int = 14,
    long_days: int = 180,
    dip_threshold: float = 0.15,
) -> ManagerForm:
    """Форма для объяснимости и мониторинга.

    Не является отдельным множителем в целевой функции назначения.
    Свежие результаты уже сильнее влияют на оценку через экспоненциальный вес истории.
    """
    as_of_d = to_date(as_of)
    from analytics.scoring import historical_data

    hist_all = historical_data(history, as_of_d)
    hist = hist_all[hist_all["manager"] == manager].copy()
    empty = ManagerForm(
        manager=manager,
        recent_metric=0.0,
        previous_metric=0.0,
        change_pct=None,
        direction="unknown",
        recent_n=0,
        previous_n=0,
        metric_name="валовая маржа на переговор",
        low_sample=True,
        comment="Недостаточно данных для оценки формы.",
        short_days=short_days,
        long_days=long_days,
    )
    if hist.empty:
        return empty

    hist["date"] = pd.to_datetime(hist["date"]).dt.date
    recent_start = as_of_d - timedelta(days=recent_days)
    prev_start = recent_start - timedelta(days=previous_days)
    short_start = as_of_d - timedelta(days=short_days)
    long_start = as_of_d - timedelta(days=long_days)

    recent = hist[(hist["date"] > recent_start) & (hist["date"] <= as_of_d)]
    previous = hist[(hist["date"] > prev_start) & (hist["date"] <= recent_start)]
    short = hist[(hist["date"] > short_start) & (hist["date"] <= as_of_d)]
    long = hist[(hist["date"] > long_start) & (hist["date"] <= as_of_d)]

    recent_m = _gm_per_negotiation(recent)
    prev_m = _gm_per_negotiation(previous)
    short_m = _gm_per_negotiation(short)
    long_m = _gm_per_negotiation(long)
    low = len(recent) < min_observations or len(previous) < min_observations

    if prev_m <= 1e-9:
        change = None
        direction = "unknown" if low else ("up" if recent_m > prev_m else "flat")
    else:
        change = (recent_m - prev_m) / prev_m * 100
        if abs(change) < 3:
            direction = "flat"
        elif change > 0:
            direction = "up"
        else:
            direction = "down"

    dip_flag = False
    if long_m > 1e-9 and len(short) >= min_observations and len(long) >= min_observations:
        dip_flag = short_m < long_m * (1.0 - dip_threshold)
        if dip_flag and direction == "flat":
            direction = "down"

    comment = (
        f"Короткое окно {short_days} дн.: {short_m:.1f} валовой маржи на переговор "
        f"({len(short)} переговоров). "
        f"Длинная база {long_days} дн.: {long_m:.1f} ({len(long)} переговоров). "
    )
    if change is not None:
        sign = "+" if change >= 0 else ""
        comment += (
            f"Сравнение соседних окон {recent_days}/{previous_days} дн.: "
            f"{sign}{change:.1f}%. "
        )
    if dip_flag:
        comment += (
            f"Замечена просадка короткого окна относительно длинной базы "
            f"(порог {dip_threshold * 100:.0f}%). "
            "В оценке заявок это уже отражается через больший вес свежей истории, "
            "без отдельного множителя «формы»."
        )
    if low:
        comment += " Выборок мало — не утверждаем статистическую значимость."

    return ManagerForm(
        manager=manager,
        recent_metric=round(recent_m, 2),
        previous_metric=round(prev_m, 2),
        change_pct=None if change is None else round(change, 1),
        direction=direction,
        recent_n=int(len(recent)),
        previous_n=int(len(previous)),
        metric_name="валовая маржа на переговор",
        low_sample=low,
        comment=comment,
        short_metric=round(short_m, 2),
        long_metric=round(long_m, 2),
        short_n=int(len(short)),
        long_n=int(len(long)),
        dip_flag=dip_flag,
        short_days=short_days,
        long_days=long_days,
    )


def forms_for_all(history: pd.DataFrame, managers: list[str], as_of, settings) -> dict[str, dict[str, Any]]:
    out = {}
    for m in managers:
        f = compute_manager_form(
            history,
            m,
            as_of,
            recent_days=settings.form_recent_days,
            previous_days=settings.form_previous_days,
            min_observations=settings.min_observations,
            short_days=getattr(settings, "form_short_days", 14),
            long_days=getattr(settings, "form_long_days", 180),
            dip_threshold=getattr(settings, "form_dip_threshold", 0.15),
        )
        out[m] = f.__dict__
    return out
