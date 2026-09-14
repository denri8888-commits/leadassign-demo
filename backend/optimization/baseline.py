"""Baseline-стратегии для сравнения экономического эффекта."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from analytics.scoring import PairScore, historical_data
from analytics.config import ModelSettings


def baseline_random(
    application_ids: list[str],
    managers: list[str],
    scores: list[PairScore],
    team_capacity: int,
    manager_capacities: dict[str, int],
    seed: int = 0,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    score_map = {(s.application_id, s.manager): s for s in scores}
    apps = list(application_ids)
    rng.shuffle(apps)
    remaining = {m: int(c) for m, c in manager_capacities.items()}
    assignments = []
    for app_id in apps:
        if len(assignments) >= team_capacity:
            break
        available = [m for m, c in remaining.items() if c > 0]
        if not available:
            break
        manager = str(rng.choice(available))
        s = score_map[(app_id, manager)]
        assignments.append(
            {
                "application_id": app_id,
                "manager": manager,
                "expected_gm": s.expected_gm,
                "method": "baseline_random",
            }
        )
        remaining[manager] -= 1
    return _pack(assignments, remaining, "baseline_random")


def baseline_best_historical(
    history: pd.DataFrame,
    applications: pd.DataFrame,
    managers: list[str],
    scores: list[PairScore],
    settings: ModelSettings,
) -> dict[str, Any]:
    """
    Простое ручное правило: каждой заявке — менеджер с лучшей исторической
    средней GM на переговор по региону+продукту (без оптимизации capacity-aware selection).
    Затем берём top team_capacity по этой оценке.
    """
    score_map = {(s.application_id, s.manager): s for s in scores}
    # историческая gm на переговор по manager×region×product — только до даты заявок
    as_of = pd.to_datetime(applications["date"].iloc[0]).date()
    hist = historical_data(history, as_of)
    if hist.empty:
        hist = history.copy()
        hist["date"] = pd.to_datetime(hist["date"]).dt.date
    hist["sale"] = hist["sale"].astype(int)
    grouped = (
        hist.groupby(["manager", "region", "product"], as_index=False)
        .agg(talks=("sale", "count"), gm_sum=("gm", "sum"))
    )
    grouped["gm_per_talk"] = grouped["gm_sum"] / grouped["talks"].clip(lower=1)

    remaining = {m: int(c) for m, c in settings.manager_capacities.items()}
    candidates = []
    for _, app in applications.iterrows():
        best_m = None
        best_v = -1.0
        sub = grouped[(grouped["region"] == app["region"]) & (grouped["product"] == app["product"])]
        for manager in managers:
            row = sub[sub["manager"] == manager]
            val = float(row["gm_per_talk"].iloc[0]) if len(row) else 0.0
            if val > best_v:
                best_v = val
                best_m = manager
        s = score_map[(str(app["application_id"]), best_m)]
        candidates.append((s.expected_gm, str(app["application_id"]), best_m, s))

    candidates.sort(reverse=True, key=lambda x: x[0])
    assignments = []
    for egm, app_id, manager, s in candidates:
        if len(assignments) >= settings.team_capacity:
            break
        # если лучший менеджер занят — ищем следующего по историческому правилу среди свободных
        pick = manager
        if remaining.get(pick, 0) <= 0:
            alts = sorted(
                [sc for sc in scores if sc.application_id == app_id and remaining.get(sc.manager, 0) > 0],
                key=lambda sc: sc.expected_gm,
                reverse=True,
            )
            if not alts:
                continue
            s = alts[0]
            pick = s.manager
            egm = s.expected_gm
        assignments.append(
            {
                "application_id": app_id,
                "manager": pick,
                "expected_gm": egm if isinstance(egm, float) else s.expected_gm,
                "method": "baseline_manual",
            }
        )
        remaining[pick] -= 1

    return _pack(assignments, remaining, "baseline_manual")


def _pack(assignments: list[dict], remaining: dict, method: str) -> dict[str, Any]:
    load: dict[str, int] = defaultdict(int)
    for a in assignments:
        load[a["manager"]] += 1
    return {
        "assignments": assignments,
        "total_expected_gm": round(sum(a["expected_gm"] for a in assignments), 2),
        "n_assigned": len(assignments),
        "manager_load": dict(load),
        "remaining_capacity": remaining,
        "method": method,
    }
