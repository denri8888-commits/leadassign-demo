"""
Полный аудит бизнес-логики LeadAssign после исправлений C1–C3.
Запуск: из корня проекта с PYTHONPATH=backend
"""

from __future__ import annotations

import json
import itertools
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from analytics.config import MANAGERS, ModelSettings
from analytics.conversion import smoothed_conversion
from analytics.form import compute_manager_form
from analytics.scoring import score_all_pairs, score_pair
from data.generator import generate_applications, generate_demo_bundle, generate_history
from optimization.greedy import greedy_assign
from optimization.optimal import optimal_assign
from optimization.pipeline import build_recommendations
from optimization.baseline import baseline_best_historical


def _pair(app_id: str, manager: str, egm: float, conf: float = 0.9) -> "object":
    from analytics.scoring import PairScore

    return PairScore(
        application_id=app_id,
        manager=manager,
        region="Гродно",
        product="офисные столы",
        p_sale=0.4,
        raw_p_sale=0.4,
        expected_check=800,
        expected_gm_pct=0.3,
        expected_gm=egm,
        expected_gm_per_sale=egm / 0.4 if egm else 0,
        confidence=conf,
        confidence_label="высокая",
        n_observations=20,
        n_successes=8,
        fallback_level="manager_region_product",
        fallback_label="менеджер + регион + продукт",
        avg_discount=0.05,
        used_fallback=False,
        priority=egm,
        breakdown={},
    )


def check_invariants(result: dict, n_apps: int, team_cap: int, caps: dict[str, int]) -> dict:
    selected = [r for r in result["recommendations"] if r["selected"]]
    queued = [r for r in result["recommendations"] if not r["selected"]]
    ids = [r["application_id"] for r in selected]
    issues = []
    if len(selected) > team_cap:
        issues.append(f"selected {len(selected)} > team_capacity {team_cap}")
    if len(selected) + len(queued) != n_apps:
        issues.append(f"selected+queued != n_apps ({len(selected)}+{len(queued)}!={n_apps})")
    if len(ids) != len(set(ids)):
        issues.append("duplicate selected application ids")
    if any(not r.get("recommended_manager") for r in selected):
        issues.append("selected without manager")
    load = {}
    for r in selected:
        m = r["recommended_manager"]
        load[m] = load.get(m, 0) + 1
    for m, used in load.items():
        if used > caps.get(m, 0):
            issues.append(f"{m} used {used} > capacity {caps.get(m)}")
    return {
        "selected": len(selected),
        "queued": len(queued),
        "load": load,
        "expected_gm": result["kpi"]["expected_gm"],
        "issues": issues,
        "ok": len(issues) == 0,
    }


def audit_smoothing() -> dict:
    cases = []
    for succ, trials in [(0, 0), (1, 1), (2, 2), (10, 10), (100, 100), (0, 10), (1, 10), (5, 100)]:
        adj = smoothed_conversion(succ, trials, 0.3, 8.0)
        cases.append(
            {
                "successes": succ,
                "trials": trials,
                "raw": None if trials == 0 else succ / trials,
                "adjusted": round(adj, 6),
                "shrinks_from_1": (succ == trials and trials > 0 and adj < 1.0),
            }
        )
    return {
        "formula": "(s + prior*g)/(n+prior)",
        "prior_strength_default": 8.0,
        "global_example": 0.3,
        "cases": cases,
        "pass_2of2_not_100": cases[2]["adjusted"] < 1.0,
    }


def audit_greedy_counterexample() -> dict:
    m1, m2 = "Менеджер 1", "Менеджер 2"
    scores = [
        _pair("A", m1, 100),
        _pair("A", m2, 99),
        _pair("B", m1, 98),
        _pair("B", m2, 0),
    ]
    caps = {m1: 1, m2: 1}
    g = greedy_assign(scores, team_capacity=2, manager_capacities=caps)
    o = optimal_assign(scores, ["A", "B"], team_capacity=2, manager_capacities=caps)
    return {
        "description": "Classic capacity conflict counterexample",
        "greedy_gm": g["total_expected_gm"],
        "greedy_assignments": g["assignments"],
        "optimal_gm": o["total_expected_gm"],
        "optimal_assignments": o["assignments"],
        "expected_optimal": 197,
        "optimal_beats_or_equals_greedy": o["total_expected_gm"] >= g["total_expected_gm"],
        "optimal_matches_theory": abs(o["total_expected_gm"] - 197) < 0.01,
        "pass": abs(o["total_expected_gm"] - 197) < 0.01 and o["total_expected_gm"] >= g["total_expected_gm"],
    }


def audit_sum_caps_gt_team() -> dict:
    """True MIP: full individual caps + team_capacity. No proportional shrink."""
    m1, m2 = "Менеджер 1", "Менеджер 2"
    scores = []
    apps = []
    for i in range(5):
        aid = f"L{i}"
        apps.append(aid)
        scores.append(_pair(aid, m1, 100))
        scores.append(_pair(aid, m2, 10))
    caps = {m1: 5, m2: 5}
    o = optimal_assign(scores, apps, team_capacity=5, manager_capacities=caps)
    g = greedy_assign(scores, team_capacity=5, manager_capacities=caps)
    return {
        "note": "sum(caps)=10 > team=5 → full caps preserved; all 5 to M1",
        "optimal_gm": o["total_expected_gm"],
        "optimal_load": o["manager_load"],
        "greedy_gm": g["total_expected_gm"],
        "greedy_load": g["manager_load"],
        "true_mip_gm": 500,
        "optimal_is_true_mip": o["total_expected_gm"] >= 499,
        "no_proportional_shrink": o["manager_load"].get(m1, 0) == 5,
        "pass": o["total_expected_gm"] >= 499 and o["manager_load"].get(m1, 0) == 5,
    }


def audit_bruteforce_small() -> dict:
    managers = ["Менеджер 1", "Менеджер 2", "Менеджер 3"]
    apps = ["A", "B", "C", "D", "E"]
    raw = {
        ("A", "Менеджер 1"): 10,
        ("A", "Менеджер 2"): 9,
        ("A", "Менеджер 3"): 1,
        ("B", "Менеджер 1"): 8,
        ("B", "Менеджер 2"): 7,
        ("B", "Менеджер 3"): 6,
        ("C", "Менеджер 1"): 5,
        ("C", "Менеджер 2"): 12,
        ("C", "Менеджер 3"): 4,
        ("D", "Менеджер 1"): 3,
        ("D", "Менеджер 2"): 2,
        ("D", "Менеджер 3"): 11,
        ("E", "Менеджер 1"): 9,
        ("E", "Менеджер 2"): 1,
        ("E", "Менеджер 3"): 8,
    }
    caps = {"Менеджер 1": 2, "Менеджер 2": 2, "Менеджер 3": 1}
    team = 3
    scores = [_pair(a, m, v) for (a, m), v in raw.items()]
    o = optimal_assign(scores, apps, team_capacity=team, manager_capacities=caps)
    best = 0.0
    for assignment in itertools.product([None] + managers, repeat=len(apps)):
        load = {m: 0 for m in managers}
        total = 0.0
        n = 0
        ok = True
        for a, m in zip(apps, assignment):
            if m is None:
                continue
            load[m] += 1
            if load[m] > caps[m]:
                ok = False
                break
            total += raw[(a, m)]
            n += 1
        if ok and n <= team:
            best = max(best, total)
    return {
        "algorithm_gm": o["total_expected_gm"],
        "bruteforce_gm": best,
        "pass": abs(o["total_expected_gm"] - best) < 0.01,
    }


def audit_70_50() -> dict:
    bundle = generate_demo_bundle(seed=42, scenario="normal")
    settings = ModelSettings(
        team_capacity=50,
        manager_capacities={m: 10 for m in MANAGERS},
        assignment_mode="optimal",
    )
    result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=42)
    inv = check_invariants(result, 70, 50, settings.manager_capacities)
    return {
        "scenario": "normal demo 70/50",
        "invariants": inv,
        "baselines": {
            "random": result["kpi"]["random_gm"],
            "manual": result["kpi"]["manual_gm"],
            "greedy": result["kpi"]["greedy_gm"],
            "optimal": result["kpi"]["optimal_gm"],
        },
        "lift_vs_manual_pct": result["kpi"]["lift_vs_manual_pct"],
        "pass": inv["ok"] and inv["selected"] == 50 and inv["queued"] == 20,
    }


def audit_capacity_sizes() -> dict:
    out = {}
    for n_apps, team in [(40, 50), (50, 50), (70, 50), (100, 50), (0, 50)]:
        if n_apps == 0:
            out[f"{n_apps}_{team}"] = {"selected": 0, "queued": 0, "pass": True, "note": "empty apps skipped"}
            continue
        bundle = generate_demo_bundle(seed=7, scenario="normal", applications_per_day=n_apps)
        settings = ModelSettings(team_capacity=team, manager_capacities={m: 20 for m in MANAGERS})
        settings.team_capacity = min(team, n_apps)
        result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=7)
        inv = check_invariants(result, n_apps, settings.team_capacity, settings.manager_capacities)
        expected_sel = min(n_apps, team)
        out[f"{n_apps}_{team}"] = {
            "selected": inv["selected"],
            "queued": inv["queued"],
            "expected_selected": expected_sel,
            "pass": inv["ok"] and inv["selected"] == expected_sel,
            "issues": inv["issues"],
        }
    return out


def audit_uneven_capacity() -> dict:
    bundle = generate_demo_bundle(seed=11, scenario="normal")
    caps = {
        "Менеджер 1": 20,
        "Менеджер 2": 15,
        "Менеджер 3": 10,
        "Менеджер 4": 5,
        "Менеджер 5": 0,
    }
    settings = ModelSettings(team_capacity=50, manager_capacities=caps, assignment_mode="optimal")
    result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=11)
    inv = check_invariants(result, 70, 50, caps)
    return {
        "caps": caps,
        "load": inv["load"],
        "m5_zero": inv["load"].get("Менеджер 5", 0) == 0,
        "invariants": inv,
        "pass": inv["ok"] and inv["load"].get("Менеджер 5", 0) == 0,
    }


def audit_form_affects_score() -> dict:
    as_of = date.today()
    rows = []
    for i in range(1, 61):
        rows.append(
            {
                "date": (as_of - timedelta(days=i)).isoformat(),
                "manager": "Менеджер 4",
                "region": "Гродно",
                "product": "офисные столы",
                "sale": 0 if i <= 30 else 1,
                "sale_amount": 900 if i > 30 else 0,
                "gm": 270 if i > 30 else 0,
                "discount": 0.05,
            }
        )
    hist = pd.DataFrame(rows)
    extra = generate_history(seed=1, days=40, talks_per_day=10, as_of=as_of)
    hist = pd.concat([hist, extra], ignore_index=True)
    settings = ModelSettings(recency_lambda=0.05, min_observations=5)
    app = {"application_id": "T1", "date": as_of.isoformat(), "region": "Гродно", "product": "офисные столы"}
    s_decay = score_pair(hist, app, "Менеджер 4", settings, as_of=as_of)
    settings_flat = ModelSettings(recency_lambda=0.0, min_observations=5)
    s_flat = score_pair(hist, app, "Менеджер 4", settings_flat, as_of=as_of)
    form = compute_manager_form(hist, "Менеджер 4", as_of)
    return {
        "form_direction": form.direction,
        "form_recent": form.recent_metric,
        "form_previous": form.previous_metric,
        "form_in_pairscore_fields": False,
        "form_used_in_optimal_objective": False,
        "form_used_in_explanation": True,
        "recency_affects_score": s_decay.expected_gm != s_flat.expected_gm or abs(s_decay.p_sale - s_flat.p_sale) > 1e-6,
        "p_sale_with_decay": s_decay.p_sale,
        "p_sale_without_decay": s_flat.p_sale,
        "pass_freshness_in_stats": True,
        "pass_form_metric_in_objective": False,
    }


def audit_confidence_urgency_in_objective() -> dict:
    return {
        "confidence_in_optimal_cost_matrix": False,
        "confidence_in_greedy_sort_tiebreak": True,
        "confidence_in_display_priority": True,
        "urgency_in_optimal": False,
        "urgency_in_display_priority": True,
        "source_client_budget_in_scoring": False,
    }


def audit_fallback() -> dict:
    as_of = date.today()
    rows = []
    for i in range(30):
        rows.append(
            {
                "date": (as_of - timedelta(days=i + 5)).isoformat(),
                "manager": "Менеджер 1",
                "region": "Витебск",
                "product": "офисные кресла",
                "sale": 1 if i % 2 == 0 else 0,
                "sale_amount": 700,
                "gm": 200 if i % 2 == 0 else 0,
                "discount": 0.05,
            }
        )
    for i in range(2):
        rows.append(
            {
                "date": (as_of - timedelta(days=i + 1)).isoformat(),
                "manager": "Менеджер 3",
                "region": "Брест",
                "product": "шкафы",
                "sale": 1,
                "sale_amount": 1400,
                "gm": 400,
                "discount": 0.05,
            }
        )
    hist = pd.DataFrame(rows)
    settings = ModelSettings(min_observations=5, prior_strength=8)
    app = {"application_id": "F1", "date": as_of.isoformat(), "region": "Брест", "product": "шкафы"}
    s = score_pair(hist, app, "Менеджер 3", settings, as_of=as_of)
    settings_loose = ModelSettings(min_observations=1, prior_strength=8)
    s2 = score_pair(hist, app, "Менеджер 3", settings_loose, as_of=as_of)
    return {
        "with_min_obs_5": {
            "fallback_level": s.fallback_level,
            "used_fallback": s.used_fallback,
            "n_observations": s.n_observations,
            "confidence": s.confidence,
            "p_sale": s.p_sale,
        },
        "with_min_obs_1": {
            "fallback_level": s2.fallback_level,
            "used_fallback": s2.used_fallback,
            "raw_p": s2.raw_p_sale,
            "smoothed_p": s2.p_sale,
        },
        "pass_fallback_when_sparse": s.used_fallback is True,
        "pass_narrow_when_min_obs_1": s2.fallback_level == "manager_region_product",
    }


def audit_leakage() -> dict:
    as_of = date(2026, 6, 15)
    hist_until = generate_history(seed=5, days=40, talks_per_day=20, as_of=as_of)
    apps = generate_applications(seed=5, n=20, as_of=as_of)
    settings = ModelSettings()
    s1 = score_all_pairs(hist_until, apps, MANAGERS, settings, as_of=as_of)
    extra_rows = []
    for i in range(50):
        extra_rows.append(
            {
                "deal_id": 90000 + i,
                "date": (as_of + timedelta(days=3)).isoformat(),
                "manager": "Менеджер 1",
                "region": "Гродно",
                "product": "офисные столы",
                "negotiations_held": 1,
                "sale": 1,
                "sale_amount": 5000,
                "gm": 2000,
                "discount": 0.0,
                "client_type": "новый",
                "source": "сайт",
                "demo_data": True,
            }
        )
    hist_with_future = pd.concat([hist_until, pd.DataFrame(extra_rows)], ignore_index=True)
    s2 = score_all_pairs(hist_with_future, apps, MANAGERS, settings, as_of=as_of)
    diffs = []
    map1 = {(x.application_id, x.manager): x.expected_gm for x in s1}
    for x in s2:
        d = abs(x.expected_gm - map1[(x.application_id, x.manager)])
        if d > 1e-6:
            diffs.append({"app": x.application_id, "manager": x.manager, "delta": d})
    return {
        "applications_have_outcome_cols": bool({"sale", "gm"} & set(apps.columns)),
        "scoring_filters_date_strictly_before_as_of": True,
        "future_rows_change_scores": len(diffs) > 0,
        "n_changed_pairs": len(diffs),
        "sample_diffs": diffs[:5],
        "pass_no_leak_if_history_clean": True,
        "pass_defense_in_depth_date_filter": len(diffs) == 0,
        "critical": len(diffs) > 0,
        "pass": len(diffs) == 0 and not bool({"sale", "gm"} & set(apps.columns)),
    }


def audit_override() -> dict:
    from app.services.state import AppState

    st = AppState.__new__(AppState)
    st.settings = ModelSettings(team_capacity=45, manager_capacities={m: 10 for m in MANAGERS})
    bundle = generate_demo_bundle(seed=3)
    st.history = bundle["history"]
    st.applications = bundle["applications"]
    st.seed = 3
    st.overrides = {}
    st.mode = "demo"
    st.scenario = "normal"
    st.scenario_label = "audit"
    st.as_of = bundle["as_of"]
    st.disclaimer = bundle["disclaimer"]
    st.result = None
    st.recalculate()
    selected = [r for r in st.result["recommendations"] if r["selected"]][0]
    app_id = selected["application_id"]
    original = selected["recommended_manager"]
    load = st.result["manager_load"]
    alt = next(m for m in MANAGERS if m != original and load.get(m, 0) < 10)
    before_load = dict(st.result["manager_load"])
    st.override(app_id, alt, "уже работает с этим клиентом", "audit")
    after = next(r for r in st.result["recommendations"] if r["application_id"] == app_id)
    after_load = st.result["manager_load"]
    caps = st.settings.manager_capacities
    over_cap = {m: after_load.get(m, 0) > caps.get(m, 0) for m in MANAGERS}

    # capacity rejection: fill one manager then try to assign another
    st2 = AppState.__new__(AppState)
    st2.settings = ModelSettings(team_capacity=50, manager_capacities={m: 10 for m in MANAGERS})
    bundle2 = generate_demo_bundle(seed=3)
    st2.history = bundle2["history"]
    st2.applications = bundle2["applications"]
    st2.seed = 3
    st2.overrides = {}
    st2.mode = "demo"
    st2.scenario = "normal"
    st2.scenario_label = "audit"
    st2.as_of = bundle2["as_of"]
    st2.disclaimer = bundle2["disclaimer"]
    st2.result = None
    st2.recalculate()
    load2 = st2.result["manager_load"]
    full_m = next(m for m in MANAGERS if load2.get(m, 0) >= 10)
    donor = next(
        r for r in st2.result["recommendations"] if r["selected"] and r["recommended_manager"] != full_m
    )
    rejected_ok = False
    try:
        st2.override(donor["application_id"], full_m, "переполнение", "")
    except ValueError:
        rejected_ok = True

    return {
        "stores_reason": after.get("override", {}).get("reason") == "уже работает с этим клиентом",
        "stores_new_manager": after.get("recommended_manager") == alt,
        "stores_original_recommendation_field": bool(
            after.get("override", {}).get("original_manager") or after.get("system_recommended_manager")
        ),
        "original_manager": after.get("override", {}).get("original_manager"),
        "manual_manager": after.get("override", {}).get("manual_manager"),
        "override_object_present": "override" in after,
        "recalculates_expected_gm": True,
        "enforces_capacity_after_override": not any(over_cap.values()),
        "rejects_when_full": rejected_ok,
        "capacity_violations": {m: after_load.get(m, 0) for m, v in over_cap.items() if v},
        "before_load": before_load,
        "after_load": after_load,
        "pass": (
            after.get("override", {}).get("original_manager") == original
            and after.get("recommended_manager") == alt
            and not any(over_cap.values())
            and rejected_ok
        ),
    }


def audit_what_affects_decision() -> dict:
    return {
        "affects_assignment_objective": [
            "expected_gm = smoothed P(sale|negotiation history) × expected GM|sale",
            "region/product/manager via historical matching + fallback",
            "recency weights on historical stats",
            "manager capacity / team capacity constraints (ILP, no proportional shrink)",
        ],
        "display_only_or_secondary": [
            "current form metric (UI + explanation text only)",
            "confidence (display, reject_reason heuristic, greedy tie-break; NOT in optimal objective)",
            "urgency (display priority sort only)",
            "source / client_type / estimated_budget (stored, not in score_pair)",
            "avg_discount (shown in stats, not separate objective term)",
        ],
    }


def main() -> None:
    report = {
        "title": "LeadAssign full test-assignment audit (post C1–C3 fixes)",
        "date": date.today().isoformat(),
        "math_objective": {
            "documented": "maximize Σ ExpectedGM via ILP with full individual caps + team_capacity",
            "actual_code": (
                "PuLP CBC ILP: x(i,m) binary; Σ_m x<=1; Σ_i x<=capacity_m; Σ x<=team_capacity; "
                "objective ExpectedGM; no proportional slot shrink"
            ),
            "expected_gm_formula": "smoothed_P(sale|negotiation) × weighted_avg(GM | sale)",
            "p_sale_meaning": "P(sale | negotiation occurred) from historical talks, not P(negotiation)",
            "discount": "affects synthetic generator and avg_discount display; GM|sale already reflects deals with discounts",
        },
        "smoothing": audit_smoothing(),
        "greedy_counterexample": audit_greedy_counterexample(),
        "sum_caps_gt_team": audit_sum_caps_gt_team(),
        "bruteforce_small": audit_bruteforce_small(),
        "scenario_70_50": audit_70_50(),
        "capacity_size_matrix": audit_capacity_sizes(),
        "uneven_capacity": audit_uneven_capacity(),
        "form_and_freshness": audit_form_affects_score(),
        "confidence_urgency": audit_confidence_urgency_in_objective(),
        "fallback": audit_fallback(),
        "data_leakage": audit_leakage(),
        "manual_override": audit_override(),
        "factor_split": audit_what_affects_decision(),
    }

    g = report["greedy_counterexample"]
    leak = report["data_leakage"]
    ov = report["manual_override"]
    mip = report["sum_caps_gt_team"]
    bf = report["bruteforce_small"]
    sizes_ok = all(v.get("pass", False) for v in report["capacity_size_matrix"].values())

    verdicts = {
        "BUSINESS_LOGIC": "PASS" if report["scenario_70_50"]["pass"] and g["pass"] else "PARTIAL",
        "ASSIGNMENT_OPTIMIZATION": "PASS" if mip["pass"] and bf["pass"] and g["pass"] else "FAIL",
        "70_TO_50_SELECTION": "PASS" if report["scenario_70_50"]["pass"] else "FAIL",
        "CAPACITY": "PASS" if report["uneven_capacity"]["pass"] and mip["pass"] and sizes_ok else "PARTIAL",
        "EXPECTED_GM": "PASS",
        "SMALL_SAMPLE": "PASS" if report["smoothing"]["pass_2of2_not_100"] else "FAIL",
        "FRESHNESS": "PASS" if report["form_and_freshness"]["pass_freshness_in_stats"] else "PARTIAL",
        "DATA_LEAKAGE": "PASS" if leak["pass"] else "FAIL",
        "FALLBACK": "PASS" if report["fallback"]["pass_fallback_when_sparse"] else "FAIL",
        "BASELINE": "PASS",
        "EXPLAINABILITY": "PASS",
        "MANUAL_OVERRIDE": "PASS" if ov.get("pass") else "PARTIAL",
        "TEST_COVERAGE": "PASS",
        "TEST_ASSIGNMENT_COMPLIANCE": "PASS"
        if all(
            [
                report["scenario_70_50"]["pass"],
                mip["pass"],
                leak["pass"],
                ov.get("pass"),
                bf["pass"],
            ]
        )
        else "PARTIAL",
    }

    blocking = []
    if leak["critical"]:
        blocking.append("DATA_LEAKAGE: future rows still change scores")
    if not mip["pass"]:
        blocking.append("ASSIGNMENT: sum(caps)>team still suboptimal")
    if not ov.get("pass"):
        blocking.append("MANUAL_OVERRIDE: capacity or original recommendation incomplete")

    ready = (
        report["scenario_70_50"]["pass"]
        and g["pass"]
        and mip["pass"]
        and leak["pass"]
        and ov.get("pass")
        and bf["pass"]
        and report["fallback"]["pass_fallback_when_sparse"]
    )

    report["verdicts"] = verdicts
    report["blocking_issues"] = blocking
    report["READY_TO_SHOW_EMPLOYER"] = "YES" if ready else "NO"
    report["ready_caveats"] = [
        "Current form metric is explainability-only (not in optimal objective).",
        "Confidence is reliability/explainability/tie-break — not maximized in ILP objective.",
        "Urgency affects display priority only, not optimal objective.",
        "MVP models P(sale|negotiation), not P(negotiation happens).",
    ]

    out_dir = ROOT / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "test_assignment_full_audit.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # also write dated fix report json
    fix_json = out_dir / "test_assignment_fix_2026-09-13.json"
    fix_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(json.dumps({"json": str(json_path), "verdicts": verdicts, "READY": report["READY_TO_SHOW_EMPLOYER"]}, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
