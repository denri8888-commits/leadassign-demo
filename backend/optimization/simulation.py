"""Симулятор сравнения ручного и автоматического распределения."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np

from analytics.config import MANAGERS, ModelSettings
from analytics.scoring import score_all_pairs
from data.generator import generate_applications, generate_history
from optimization.baseline import baseline_best_historical, baseline_random
from optimization.optimal import optimal_assign


def run_simulation(
    days: int = 14,
    auto_share: float = 0.5,
    seed: int = 42,
    settings: ModelSettings | None = None,
) -> dict[str, Any]:
    """
    Упрощённый симулятор на синтетике.
    Не заявляет статистическую значимость без формального расчёта.
    """
    settings = settings or ModelSettings()
    rng = np.random.default_rng(seed)
    auto_days = 0
    manual_days = 0
    auto_gm = 0.0
    manual_gm = 0.0
    auto_processed = 0
    manual_processed = 0
    total_apps = 0
    daily = []

    for d in range(days):
        day = date.today() - timedelta(days=days - d)
        hist = generate_history(seed=seed + d, days=90, as_of=day, scenario="normal")
        apps = generate_applications(seed=seed + 100 + d, n=settings.applications_per_day, as_of=day)
        scores = score_all_pairs(hist, apps, MANAGERS, settings, as_of=day)
        app_ids = [str(x) for x in apps["application_id"].tolist()]

        use_auto = rng.random() < auto_share
        if use_auto:
            res = optimal_assign(scores, app_ids, settings.team_capacity, settings.manager_capacities)
            auto_days += 1
            auto_gm += res["total_expected_gm"]
            auto_processed += res["n_assigned"]
            mode = "auto"
            gm = res["total_expected_gm"]
            processed = res["n_assigned"]
        else:
            res = baseline_best_historical(hist, apps, MANAGERS, scores, settings)
            manual_days += 1
            manual_gm += res["total_expected_gm"]
            manual_processed += res["n_assigned"]
            mode = "manual"
            gm = res["total_expected_gm"]
            processed = res["n_assigned"]

        # для сравнения всегда считаем оба на каждом дне
        opt = optimal_assign(scores, app_ids, settings.team_capacity, settings.manager_capacities)
        man = baseline_best_historical(hist, apps, MANAGERS, scores, settings)
        rnd = baseline_random(app_ids, MANAGERS, scores, settings.team_capacity, settings.manager_capacities, seed=seed + d)

        total_apps += len(apps)
        daily.append(
            {
                "day": day.isoformat(),
                "mode": mode,
                "selected_gm": gm,
                "optimized_gm": opt["total_expected_gm"],
                "manual_gm": man["total_expected_gm"],
                "random_gm": rnd["total_expected_gm"],
                "processed": processed,
                "applications": len(apps),
            }
        )

    opt_total = sum(x["optimized_gm"] for x in daily)
    man_total = sum(x["manual_gm"] for x in daily)
    rnd_total = sum(x["random_gm"] for x in daily)
    diff = opt_total - man_total
    avg_change = diff / days if days else 0

    return {
        "days": days,
        "auto_share": auto_share,
        "auto_days": auto_days,
        "manual_days": manual_days,
        "gm_manual_total": round(man_total, 2),
        "gm_optimized_total": round(opt_total, 2),
        "gm_random_total": round(rnd_total, 2),
        "difference_opt_vs_manual": round(diff, 2),
        "avg_daily_change": round(avg_change, 2),
        "applications_total": total_apps,
        "processed_auto": auto_processed,
        "processed_manual": manual_processed,
        "daily": daily,
        "note": (
            "На демонстрационных данных прототип показывает потенциальный прирост. "
            "Реальный эффект необходимо проверить на исторических и текущих данных компании. "
            "Симуляция не является доказательством статистической значимости."
        ),
    }
