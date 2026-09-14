"""Анализ сценариев capacity и экономика найма."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from analytics.config import ModelSettings
from analytics.scoring import PairScore


def analyze_capacity_scenarios(
    scores: list[PairScore],
    application_ids: list[str],
    base_settings: ModelSettings,
    assign_fn: Callable,
    levels: list[int] | None = None,
) -> dict[str, Any]:
    """
    Сценарии 40..70 переговоров.
    Этап 2 / стратегическая аналитика — не смешивать с обязательным MVP-распределением.
    """
    levels = levels or [40, 45, 50, 55, 60, 65, 70]
    base_gm = None
    rows = []
    for cap in levels:
        settings = deepcopy(base_settings)
        settings.team_capacity = min(cap, len(application_ids))
        # масштабируем индивидуальные лимиты пропорционально, сохраняя гибкость
        total_indiv = sum(settings.manager_capacities.values()) or 1
        scale = settings.team_capacity / total_indiv
        settings.manager_capacities = {
            m: max(1, int(round(c * scale))) for m, c in base_settings.manager_capacities.items()
        }
        # подгонка суммы
        while sum(settings.manager_capacities.values()) > settings.team_capacity:
            m = max(settings.manager_capacities, key=settings.manager_capacities.get)
            if settings.manager_capacities[m] > 1:
                settings.manager_capacities[m] -= 1
            else:
                break

        result = assign_fn(scores, application_ids, settings.team_capacity, settings.manager_capacities)
        gm = result["total_expected_gm"]
        if base_gm is None:
            base_gm = gm
        delta = gm - (rows[-1]["expected_gm"] if rows else gm)
        rows.append(
            {
                "capacity": cap,
                "processed": result["n_assigned"],
                "expected_gm": gm,
                "delta_gm": round(delta if rows else 0.0, 2),
                "extra_vs_50": round(gm - next((r["expected_gm"] for r in rows if r["capacity"] == 50), gm), 2)
                if any(r["capacity"] == 50 for r in rows) or cap == 50
                else None,
            }
        )

    # пересчёт extra_vs_50 после полного прохода
    gm50 = next((r["expected_gm"] for r in rows if r["capacity"] == 50), rows[0]["expected_gm"])
    for r in rows:
        r["extra_vs_50"] = round(r["expected_gm"] - gm50, 2)
        r["extra_talks_vs_50"] = r["capacity"] - 50

    # экономика найма (демонстрационная)
    gm70 = next((r["expected_gm"] for r in rows if r["capacity"] == 70), rows[-1]["expected_gm"])
    daily_uplift = gm70 - gm50
    monthly_uplift = daily_uplift * base_settings.working_days_per_month
    cost = base_settings.extra_manager_monthly_cost
    payback_days = None
    if daily_uplift > 0:
        payback_days = round(cost / daily_uplift, 1)

    return {
        "scenarios": rows,
        "diminishing_returns_note": (
            "Дополнительная ёмкость постепенно приносит меньший прирост, "
            "потому что лучшие заявки уже обработаны."
        ),
        "hiring_economics": {
            "stage": "Этап 2 / стратегическая аналитика",
            "daily_gm_uplift_50_to_70": round(daily_uplift, 2),
            "monthly_gm_uplift_estimate": round(monthly_uplift, 2),
            "extra_manager_monthly_cost": cost,
            "net_monthly_estimate": round(monthly_uplift - cost, 2),
            "payback_days_estimate": payback_days,
            "disclaimer": (
                "Это демонстрационный параметр. Реальное значение должно быть заменено "
                "финансовыми данными компании. При текущих предположениях увеличение capacity "
                "может быть экономически оправдано — решение принимает руководитель."
            ),
        },
        "chart": {
            "x_label": "Количество переговоров",
            "y_label": "Ожидаемая GM",
            "points": [{"x": r["capacity"], "y": r["expected_gm"]} for r in rows],
        },
    }
