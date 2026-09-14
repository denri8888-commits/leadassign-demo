"""Оркестрация полного расчёта рекомендаций."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from analytics.config import MANAGERS, ModelSettings
from analytics.explanation import explain_recommendation
from analytics.form import forms_for_all
from analytics.scoring import PairScore, score_all_pairs
from data.validation import validate_applications, validate_history, validate_settings
from optimization.baseline import baseline_best_historical, baseline_random
from optimization.capacity_analysis import analyze_capacity_scenarios
from optimization.greedy import greedy_assign
from optimization.optimal import optimal_assign


def _reject_reason(app_id: str, scores: list[PairScore], assigned_ids: set[str], best_assigned_gm: float) -> str:
    app_scores = [s for s in scores if s.application_id == app_id]
    if not app_scores:
        return "недостаточно данных для оценки"
    best = max(app_scores, key=lambda s: s.expected_gm)
    if best.confidence_label == "низкая" and best.expected_gm < best_assigned_gm * 0.7:
        return "мало похожих случаев и относительно низкая ожидаемая валовая маржа"
    if best.expected_gm < best_assigned_gm * 0.85:
        return "ожидаемая валовая маржа ниже, чем у заявок, которые уже вошли в загрузку"
    return "места в дневной загрузке заняты более выгодными заявками"


def build_recommendations(
    history: pd.DataFrame,
    applications: pd.DataFrame,
    settings: ModelSettings,
    seed: int = 42,
) -> dict[str, Any]:
    hist_errors = validate_history(history)
    app_errors = validate_applications(applications)
    set_errors = validate_settings(settings, len(applications))
    errors = hist_errors + app_errors + set_errors
    if errors:
        raise ValueError("; ".join(errors))

    as_of = pd.to_datetime(applications["date"].iloc[0]).date()
    scores = score_all_pairs(history, applications, MANAGERS, settings, as_of=as_of)
    app_ids = [str(x) for x in applications["application_id"].tolist()]

    if settings.assignment_mode == "greedy":
        primary = greedy_assign(scores, settings.team_capacity, settings.manager_capacities)
    else:
        primary = optimal_assign(scores, app_ids, settings.team_capacity, settings.manager_capacities)

    greedy = greedy_assign(scores, settings.team_capacity, settings.manager_capacities)
    optimal = optimal_assign(scores, app_ids, settings.team_capacity, settings.manager_capacities)
    base_random = baseline_random(
        app_ids, MANAGERS, scores, settings.team_capacity, settings.manager_capacities, seed=seed
    )
    base_manual = baseline_best_historical(history, applications, MANAGERS, scores, settings)

    assigned_map = {a["application_id"]: a for a in primary["assignments"]}
    assigned_ids = set(assigned_map)
    best_assigned_gm = max((a["expected_gm"] for a in primary["assignments"]), default=0.0)

    score_by_app: dict[str, list[PairScore]] = {}
    for s in scores:
        score_by_app.setdefault(s.application_id, []).append(s)

    forms = forms_for_all(history, MANAGERS, as_of, settings)

    recommendations = []
    for _, app in applications.iterrows():
        app_id = str(app["application_id"])
        app_scores = sorted(score_by_app[app_id], key=lambda x: x.expected_gm, reverse=True)
        selected = app_id in assigned_ids
        chosen_manager = assigned_map[app_id]["manager"] if selected else app_scores[0].manager
        chosen = next(s for s in app_scores if s.manager == chosen_manager)
        alts = [s for s in app_scores if s.manager != chosen_manager]
        explanation = explain_recommendation(chosen, alts, forms.get(chosen_manager), capacity_ok=selected)

        # приоритет — только для сортировки в таблице; в оптимизацию не входит
        best_possible = app_scores[0]
        urgency_boost = 1.08 if str(app.get("urgency", "")) == "высокая" else 1.0
        priority = best_possible.expected_gm * (0.5 + 0.5 * best_possible.confidence) * urgency_boost
        form_info = forms.get(chosen_manager) or forms.get(best_possible.manager)

        recommendations.append(
            {
                "application_id": app_id,
                "date": str(app["date"]),
                "region": app["region"],
                "product": app["product"],
                "source": app.get("source"),
                "client_type": app.get("client_type"),
                "urgency": app.get("urgency"),
                "estimated_budget": app.get("estimated_budget"),
                "selected": selected,
                "recommended_manager": chosen.manager if selected else None,
                "expected_gm": chosen.expected_gm if selected else best_possible.expected_gm,
                "p_sale": chosen.p_sale if selected else best_possible.p_sale,
                "expected_check": chosen.expected_check if selected else best_possible.expected_check,
                "expected_gm_per_sale": (
                    chosen.expected_gm_per_sale if selected else best_possible.expected_gm_per_sale
                ),
                "confidence": chosen.confidence if selected else best_possible.confidence,
                "confidence_label": chosen.confidence_label if selected else best_possible.confidence_label,
                "n_observations": chosen.n_observations if selected else best_possible.n_observations,
                "priority": round(priority, 2),
                "reject_reason": None if selected else _reject_reason(app_id, scores, assigned_ids, best_assigned_gm),
                "fallback_label": chosen.fallback_label,
                "used_fallback": chosen.used_fallback,
                "explanation": explanation,
                "manager_form": form_info,
                "all_manager_scores": [s.to_dict() for s in app_scores],
            }
        )

    for r in recommendations:
        best = max(score_by_app[r["application_id"]], key=lambda s: s.expected_gm)
        r["best_available_manager"] = best.manager
        r["best_available_gm"] = best.expected_gm
        mgr = r.get("recommended_manager") or r["best_available_manager"]
        cap = int(settings.manager_capacities.get(mgr, 0))
        used = int(primary["manager_load"].get(mgr, 0))
        r["manager_capacity"] = cap
        r["manager_load"] = used
        r["free_capacity"] = max(0, cap - used)

    recommendations.sort(key=lambda r: (not r["selected"], -r["priority"]))

    opt_gm = primary["total_expected_gm"]
    manual_gm = base_manual["total_expected_gm"]
    random_gm = base_random["total_expected_gm"]
    lift_vs_manual = ((opt_gm - manual_gm) / manual_gm * 100) if manual_gm else 0.0

    capacity = analyze_capacity_scenarios(
        scores,
        app_ids,
        settings,
        assign_fn=lambda sc, ids, cap, caps: optimal_assign(sc, ids, cap, caps),
    )

    matrix = _region_product_matrix(scores)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "calculation_version": "mvp-1.0",
        "settings": settings.to_dict(),
        "disclaimer": (
            "Показатели рассчитаны на демонстрационных данных. "
            "На демонстрационных данных прототип показывает потенциальный прирост "
            f"{lift_vs_manual:.1f}% к простому ручному baseline. "
            "Реальный эффект необходимо проверить на исторических и текущих данных компании."
        ),
        "kpi": {
            "total_applications": len(applications),
            "recommended": primary["n_assigned"],
            "queued": len(applications) - primary["n_assigned"],
            "expected_gm": opt_gm,
            "avg_gm_per_talk": round(opt_gm / primary["n_assigned"], 2) if primary["n_assigned"] else 0,
            "lift_vs_manual_pct": round(lift_vs_manual, 1),
            "lift_vs_manual_abs": round(opt_gm - manual_gm, 2),
            "manual_gm": manual_gm,
            "random_gm": random_gm,
            "greedy_gm": greedy["total_expected_gm"],
            "optimal_gm": optimal["total_expected_gm"],
        },
        "manager_load": primary["manager_load"],
        "baselines": {
            "random": base_random,
            "manual": base_manual,
            "greedy": greedy,
            "optimal": optimal,
        },
        "forms": forms,
        "recommendations": recommendations,
        "capacity_analysis": capacity,
        "matrix": matrix,
        "charts": {
            "gm_comparison": [
                {"name": "Случайный", "value": random_gm},
                {"name": "Простой вариант", "value": manual_gm},
                {"name": "Жадный", "value": greedy["total_expected_gm"]},
                {"name": "Оптимизация", "value": optimal["total_expected_gm"]},
            ],
            "load": [{"manager": m, "load": primary["manager_load"].get(m, 0), "capacity": settings.manager_capacities.get(m, 0)} for m in MANAGERS],
            "by_region": _agg_selected(recommendations, "region"),
            "by_product": _agg_selected(recommendations, "product"),
            "form_series": [
                {
                    "manager": m,
                    "recent": forms[m]["recent_metric"],
                    "previous": forms[m]["previous_metric"],
                    "change_pct": forms[m]["change_pct"],
                }
                for m in MANAGERS
            ],
        },
        "core_idea": (
            "Система не ищет лучшего менеджера вообще. Она ищет лучшее назначение "
            "конкретной заявки конкретному менеджеру с учётом ожидаемого экономического "
            "результата и ограниченной мощности команды."
        ),
    }
    return result


def _agg_selected(recs: list[dict], key: str) -> list[dict]:
    buckets: dict[str, float] = {}
    for r in recs:
        if not r["selected"]:
            continue
        buckets[r[key]] = buckets.get(r[key], 0.0) + float(r["expected_gm"])
    return [{"name": k, "expected_gm": round(v, 2)} for k, v in buckets.items()]


def _region_product_matrix(scores: list[PairScore]) -> list[dict]:
    # average expected gm by manager × region × product
    from collections import defaultdict

    acc: dict[tuple, list[float]] = defaultdict(list)
    conf: dict[tuple, list[float]] = defaultdict(list)
    nobs: dict[tuple, list[float]] = defaultdict(list)
    for s in scores:
        key = (s.manager, s.region, s.product)
        acc[key].append(s.expected_gm)
        conf[key].append(s.confidence)
        nobs[key].append(s.n_observations)
    rows = []
    for (manager, region, product), vals in acc.items():
        rows.append(
            {
                "manager": manager,
                "region": region,
                "product": product,
                "expected_gm": round(sum(vals) / len(vals), 2),
                "confidence": round(sum(conf[(manager, region, product)]) / len(vals), 3),
                "n_observations": round(sum(nobs[(manager, region, product)]) / len(vals), 1),
            }
        )
    return rows
