"""Жадный алгоритм назначения."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from analytics.scoring import PairScore


def greedy_assign(
    scores: list[PairScore],
    team_capacity: int,
    manager_capacities: dict[str, int],
) -> dict[str, Any]:
    """
    1. Сортируем все пары по expected_gm убыв.
    2. Назначаем, если заявка свободна и у менеджера есть capacity.
    3. Останавливаемся при team_capacity.
    """
    remaining = {m: int(c) for m, c in manager_capacities.items()}
    assigned_apps: set[str] = set()
    assignments: list[dict[str, Any]] = []
    sorted_scores = sorted(scores, key=lambda s: (s.expected_gm, s.confidence), reverse=True)

    for s in sorted_scores:
        if len(assignments) >= team_capacity:
            break
        if s.application_id in assigned_apps:
            continue
        if remaining.get(s.manager, 0) <= 0:
            continue
        assignments.append(
            {
                "application_id": s.application_id,
                "manager": s.manager,
                "expected_gm": s.expected_gm,
                "confidence": s.confidence,
                "p_sale": s.p_sale,
                "method": "greedy",
            }
        )
        assigned_apps.add(s.application_id)
        remaining[s.manager] -= 1

    total_gm = sum(a["expected_gm"] for a in assignments)
    load = defaultdict(int)
    for a in assignments:
        load[a["manager"]] += 1

    return {
        "assignments": assignments,
        "total_expected_gm": round(total_gm, 2),
        "n_assigned": len(assignments),
        "manager_load": dict(load),
        "remaining_capacity": remaining,
        "method": "greedy",
    }
