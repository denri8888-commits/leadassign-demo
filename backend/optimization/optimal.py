"""Оптимальное назначение: ILP (PuLP/CBC) с полными individual caps и team_capacity."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from analytics.scoring import PairScore


def _pick_solver():
    """Выбрать доступный MIP-solver (локально CBC, на Vercel — CBC/HiGHS)."""
    import pulp

    candidates = []
    if hasattr(pulp, "COIN_CMD"):
        try:
            candidates.append(pulp.COIN_CMD(msg=False, timeLimit=30))
        except Exception:
            pass
    if hasattr(pulp, "PULP_CBC_CMD"):
        try:
            candidates.append(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))
        except Exception:
            pass
    if hasattr(pulp, "HiGHS"):
        try:
            candidates.append(pulp.HiGHS(msg=False, timeLimit=30))
        except Exception:
            pass
    if hasattr(pulp, "HiGHS_CMD"):
        try:
            candidates.append(pulp.HiGHS_CMD(msg=False, timeLimit=30))
        except Exception:
            pass

    for solver in candidates:
        try:
            if solver is not None and solver.available():
                return solver
        except Exception:
            continue
    return None


def optimal_assign(
    scores: list[PairScore],
    application_ids: list[str],
    team_capacity: int,
    manager_capacities: dict[str, int],
) -> dict[str, Any]:
    """
    maximize Σ ExpectedGM(i,m) * x(i,m)

    s.t.
      Σ_m x(i,m) <= 1                 для каждой заявки
      Σ_i x(i,m) <= capacity_m        для каждого менеджера (полные лимиты)
      Σ_{i,m} x(i,m) <= team_capacity
      x ∈ {0,1}

    Не использует пропорциональное усечение слотов.
    """
    import pulp

    caps = {m: max(0, int(c)) for m, c in manager_capacities.items()}
    managers = [m for m, c in caps.items() if c > 0]
    apps = list(application_ids)
    if not apps or not managers or team_capacity <= 0:
        return {
            "assignments": [],
            "total_expected_gm": 0.0,
            "n_assigned": 0,
            "manager_load": {},
            "remaining_capacity": dict(manager_capacities),
            "method": "optimal",
        }

    score_map: dict[tuple[str, str], PairScore] = {(s.application_id, s.manager): s for s in scores}
    egm = {
        (a, m): float(score_map[(a, m)].expected_gm) if (a, m) in score_map else 0.0
        for a in apps
        for m in managers
    }

    prob = pulp.LpProblem("lead_assign", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("x", (apps, managers), lowBound=0, upBound=1, cat="Binary")
    prob += pulp.lpSum(egm[(a, m)] * x[a][m] for a in apps for m in managers)

    for a in apps:
        prob += pulp.lpSum(x[a][m] for m in managers) <= 1, f"app_{a}"
    for m in managers:
        prob += pulp.lpSum(x[a][m] for a in apps) <= caps[m], f"cap_{m}"
    prob += pulp.lpSum(x[a][m] for a in apps for m in managers) <= int(team_capacity), "team"

    status = prob.solve(_pick_solver())
    if pulp.LpStatus[status] != "Optimal":
        from optimization.greedy import greedy_assign

        out = greedy_assign(scores, team_capacity, manager_capacities)
        out["method"] = "optimal_fallback_greedy"
        return out

    assignments: list[dict[str, Any]] = []
    for a in apps:
        for m in managers:
            if pulp.value(x[a][m]) is not None and pulp.value(x[a][m]) > 0.5:
                s = score_map[(a, m)]
                assignments.append(
                    {
                        "application_id": a,
                        "manager": m,
                        "expected_gm": s.expected_gm,
                        "confidence": s.confidence,
                        "p_sale": s.p_sale,
                        "method": "optimal",
                    }
                )

    total_gm = sum(a["expected_gm"] for a in assignments)
    load: dict[str, int] = defaultdict(int)
    for a in assignments:
        load[a["manager"]] += 1

    remaining = {m: int(c) for m, c in manager_capacities.items()}
    for m, used in load.items():
        remaining[m] = remaining.get(m, 0) - used

    return {
        "assignments": assignments,
        "total_expected_gm": round(total_gm, 2),
        "n_assigned": len(assignments),
        "manager_load": dict(load),
        "remaining_capacity": remaining,
        "method": "optimal",
    }
