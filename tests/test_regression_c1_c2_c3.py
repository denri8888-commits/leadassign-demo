"""Regression tests: C1 leakage, C2 optimal caps, C3 manual override."""

from __future__ import annotations

import itertools
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from analytics.config import MANAGERS, ModelSettings
from analytics.scoring import PairScore, historical_data, score_all_pairs, score_pair
from data.generator import generate_applications, generate_demo_bundle, generate_history
from optimization.baseline import baseline_best_historical
from optimization.optimal import optimal_assign
from optimization.pipeline import build_recommendations
from app.services.state import AppState


def _snapshot_scores(scores: list[PairScore]) -> list[tuple]:
    return sorted(
        (
            s.application_id,
            s.manager,
            round(s.expected_gm, 8),
            round(s.p_sale, 8),
            round(s.expected_gm_per_sale, 8),
            round(s.confidence, 8),
            s.fallback_level,
            s.used_fallback,
        )
        for s in scores
    )


def test_future_rows_do_not_change_prediction():
    as_of = date(2026, 6, 15)
    hist = generate_history(seed=5, days=40, talks_per_day=20, as_of=as_of)
    apps = generate_applications(seed=5, n=20, as_of=as_of)
    settings = ModelSettings()
    s1 = score_all_pairs(hist, apps, MANAGERS, settings, as_of=as_of)
    extra = []
    for i in range(50):
        extra.append(
            {
                "deal_id": 90000 + i,
                "date": (as_of + timedelta(days=3 + i % 8)).isoformat(),
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
    hist_future = pd.concat([hist, pd.DataFrame(extra)], ignore_index=True)
    s2 = score_all_pairs(hist_future, apps, MANAGERS, settings, as_of=as_of)
    assert _snapshot_scores(s1) == _snapshot_scores(s2)


def test_no_future_leakage_only_future_history():
    as_of = date(2026, 6, 15)
    future_only = pd.DataFrame(
        [
            {
                "date": (as_of + timedelta(days=d)).isoformat(),
                "manager": "Менеджер 2",
                "region": "Брест",
                "product": "шкафы",
                "sale": 1,
                "sale_amount": 9999,
                "gm": 4000,
                "discount": 0.0,
            }
            for d in range(1, 21)
        ]
    )
    settings = ModelSettings()
    app = {
        "application_id": "FUT1",
        "date": as_of.isoformat(),
        "region": "Брест",
        "product": "шкафы",
    }
    s = score_pair(future_only, app, "Менеджер 2", settings, as_of=as_of)
    assert s.n_observations == 0 or s.used_fallback or s.raw_p_sale is None
    assert abs(s.expected_gm_per_sale - 4000) > 1.0 or s.n_observations == 0


def test_baseline_no_future_leakage():
    as_of = date(2026, 6, 15)
    hist = generate_history(seed=8, days=30, talks_per_day=15, as_of=as_of)
    apps = generate_applications(seed=8, n=15, as_of=as_of)
    settings = ModelSettings()
    scores = score_all_pairs(hist, apps, MANAGERS, settings, as_of=as_of)
    b1 = baseline_best_historical(hist, apps, MANAGERS, scores, settings)
    extra = pd.DataFrame(
        [
            {
                "date": (as_of + timedelta(days=2)).isoformat(),
                "manager": m,
                "region": "Гродно",
                "product": "офисные столы",
                "sale": 1,
                "sale_amount": 3000,
                "gm": 1200,
                "discount": 0.0,
            }
            for m in MANAGERS
            for _ in range(10)
        ]
    )
    hist2 = pd.concat([hist, extra], ignore_index=True)
    b2 = baseline_best_historical(hist2, apps, MANAGERS, scores, settings)
    assert b1["total_expected_gm"] == b2["total_expected_gm"]
    assert b1["assignments"] == b2["assignments"]


def test_historical_data_strict_before_as_of():
    as_of = date(2026, 1, 10)
    df = pd.DataFrame({"date": ["2026-01-09", "2026-01-10", "2026-01-11"], "sale": [1, 1, 1]})
    out = historical_data(df, as_of)
    assert list(out["date"]) == [date(2026, 1, 9)]


def _make_pair(app_id: str, manager: str, egm: float) -> PairScore:
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
        confidence=0.9,
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


def test_optimal_assignment_respects_full_manager_caps():
    m1, m2 = "Менеджер 1", "Менеджер 2"
    apps = [f"L{i}" for i in range(5)]
    scores = []
    for a in apps:
        scores.append(_make_pair(a, m1, 100))
        scores.append(_make_pair(a, m2, 10))
    out = optimal_assign(scores, apps, team_capacity=5, manager_capacities={m1: 5, m2: 5})
    assert out["total_expected_gm"] == pytest.approx(500, abs=0.01)
    assert out["manager_load"].get(m1, 0) == 5
    assert out["manager_load"].get(m2, 0) == 0


def test_team_capacity_less_than_sum_manager_caps():
    managers = ["Менеджер 1", "Менеджер 2", "Менеджер 3"]
    apps = [f"A{i}" for i in range(10)]
    scores = []
    for a in apps:
        scores.append(_make_pair(a, managers[0], 50))
        scores.append(_make_pair(a, managers[1], 5))
        scores.append(_make_pair(a, managers[2], 1))
    caps = {m: 10 for m in managers}
    out = optimal_assign(scores, apps, team_capacity=10, manager_capacities=caps)
    assert out["n_assigned"] == 10
    assert out["manager_load"].get(managers[0], 0) == 10
    assert out["total_expected_gm"] == pytest.approx(500, abs=0.01)


def test_optimal_unequal_caps_no_proportional_shrink():
    caps = {
        "Менеджер 1": 20,
        "Менеджер 2": 15,
        "Менеджер 3": 10,
        "Менеджер 4": 5,
        "Менеджер 5": 0,
    }
    apps = [f"U{i}" for i in range(40)]
    scores = []
    for a in apps:
        for m, egm in zip(MANAGERS, [40, 30, 20, 10, 1]):
            scores.append(_make_pair(a, m, egm))
    out = optimal_assign(scores, apps, team_capacity=30, manager_capacities=caps)
    load = out["manager_load"]
    assert load.get("Менеджер 5", 0) == 0
    assert load.get("Менеджер 1", 0) <= 20
    assert load.get("Менеджер 2", 0) <= 15
    assert load.get("Менеджер 3", 0) <= 10
    assert load.get("Менеджер 4", 0) <= 5
    assert out["n_assigned"] <= 30
    assert load.get("Менеджер 1", 0) == 20
    assert out["n_assigned"] == 30


def test_sum_caps_less_than_team_uses_real_caps():
    m1, m2 = "Менеджер 1", "Менеджер 2"
    apps = [f"D{i}" for i in range(10)]
    scores = []
    for a in apps:
        scores.append(_make_pair(a, m1, 10))
        scores.append(_make_pair(a, m2, 9))
    caps = {m1: 3, m2: 2}
    out = optimal_assign(scores, apps, team_capacity=20, manager_capacities=caps)
    assert out["n_assigned"] == 5
    assert out["manager_load"].get(m1, 0) <= 3
    assert out["manager_load"].get(m2, 0) <= 2


def test_sum_caps_equal_team_compatible():
    caps = {m: 10 for m in MANAGERS}
    apps = [f"E{i}" for i in range(50)]
    scores = []
    for a in apps:
        for i, m in enumerate(MANAGERS):
            scores.append(_make_pair(a, m, 20 - i))
    out = optimal_assign(scores, apps, team_capacity=50, manager_capacities=caps)
    assert out["n_assigned"] == 50
    for m in MANAGERS:
        assert out["manager_load"].get(m, 0) <= 10


def _bruteforce_optimum(apps, managers, egm, caps, team_capacity):
    best = 0.0
    choices = [None] + managers
    for assignment in itertools.product(choices, repeat=len(apps)):
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
            total += egm[(a, m)]
            n += 1
        if not ok or n > team_capacity:
            continue
        best = max(best, total)
    return best


def test_optimal_assignment_matches_bruteforce_small_case():
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
    scores = [_make_pair(a, m, v) for (a, m), v in raw.items()]
    out = optimal_assign(scores, apps, team_capacity=team, manager_capacities=caps)
    bf = _bruteforce_optimum(apps, managers, raw, caps, team)
    assert out["total_expected_gm"] == pytest.approx(bf, abs=0.01)


def test_manual_override_respects_capacity():
    st = AppState.__new__(AppState)
    st.settings = ModelSettings(team_capacity=50, manager_capacities={m: 10 for m in MANAGERS})
    bundle = generate_demo_bundle(seed=3)
    st.history = bundle["history"]
    st.applications = bundle["applications"]
    st.seed = 3
    st.overrides = {}
    st.mode = "demo"
    st.scenario = "normal"
    st.scenario_label = "t"
    st.as_of = bundle["as_of"]
    st.disclaimer = bundle["disclaimer"]
    st.result = None
    st.recalculate()
    load = st.result["manager_load"]
    full_m = next(m for m in MANAGERS if load.get(m, 0) >= 10)
    donor = next(
        r for r in st.result["recommendations"] if r["selected"] and r["recommended_manager"] != full_m
    )
    with pytest.raises(ValueError, match="capacity"):
        st.override(donor["application_id"], full_m, "тест переполнения", "")
    st.recalculate()
    assert st.result["manager_load"].get(full_m, 0) <= 10


def test_manual_override_preserves_original_recommendation():
    st = AppState.__new__(AppState)
    # team 45 при caps 10×5 → есть свободные слоты для reassignment
    st.settings = ModelSettings(team_capacity=45, manager_capacities={m: 10 for m in MANAGERS})
    bundle = generate_demo_bundle(seed=4)
    st.history = bundle["history"]
    st.applications = bundle["applications"]
    st.seed = 4
    st.overrides = {}
    st.mode = "demo"
    st.scenario = "normal"
    st.scenario_label = "t"
    st.as_of = bundle["as_of"]
    st.disclaimer = ""
    st.result = None
    st.recalculate()
    selected = next(r for r in st.result["recommendations"] if r["selected"])
    original = selected["recommended_manager"]
    load = st.result["manager_load"]
    alt = next(m for m in MANAGERS if m != original and load.get(m, 0) < 10)
    st.override(selected["application_id"], alt, "уже работает с клиентом", "комментарий")
    after = next(r for r in st.result["recommendations"] if r["application_id"] == selected["application_id"])
    ov = after["override"]
    assert ov["original_manager"] == original
    assert ov["manual_manager"] == alt
    assert ov["reason"] == "уже работает с клиентом"
    assert ov["comment"] == "комментарий"
    assert ov.get("timestamp")
    assert after["system_recommended_manager"] == original
    assert after["recommended_manager"] == alt


def test_manual_override_ui_fields_present():
    st = AppState.__new__(AppState)
    st.settings = ModelSettings(team_capacity=45, manager_capacities={m: 10 for m in MANAGERS})
    bundle = generate_demo_bundle(seed=4)
    st.history = bundle["history"]
    st.applications = bundle["applications"]
    st.seed = 4
    st.overrides = {}
    st.mode = "demo"
    st.scenario = "normal"
    st.scenario_label = "t"
    st.as_of = bundle["as_of"]
    st.disclaimer = ""
    st.result = None
    st.recalculate()
    selected = next(r for r in st.result["recommendations"] if r["selected"])
    original = selected["recommended_manager"]
    load = st.result["manager_load"]
    alt = next(m for m in MANAGERS if m != original and load.get(m, 0) < 10)
    st.override(selected["application_id"], alt, "причина UI", "коммент")
    after = next(r for r in st.result["recommendations"] if r["application_id"] == selected["application_id"])
    assert after["override"]["original_manager"] == original
    assert after["override"]["manual_manager"] == alt
    assert after["override"]["reason"] == "причина UI"

def test_form_short_long_windows_and_card_fields():
    from analytics.form import compute_manager_form

    bundle = generate_demo_bundle(seed=42, scenario="normal")
    settings = ModelSettings()
    form = compute_manager_form(
        bundle["history"],
        "Менеджер 1",
        bundle["as_of"],
        short_days=settings.form_short_days,
        long_days=settings.form_long_days,
        dip_threshold=settings.form_dip_threshold,
    )
    assert form.short_days == 14
    assert form.long_days == 180
    assert "short_metric" in form.__dict__
    assert "dip_flag" in form.__dict__

    result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=42)
    assert result["kpi"]["expected_gm"] == 6074.34
    row = next(r for r in result["recommendations"] if r["application_id"] == "A1033")
    assert row["expected_gm"] == 91.51
    assert row["priority"] == 89.59
    assert row["manager_form"] is not None
    assert "free_capacity" in row


def test_half_life_setting_updates_lambda_without_breaking_default():
    default = ModelSettings()
    assert default.recency_lambda == 0.03
    s = ModelSettings.from_dict({"recency_half_life_days": 30})
    assert abs(s.recency_half_life_days - 30) < 1e-9
    assert abs(s.recency_lambda - (0.693147 / 30)) < 1e-3
    s2 = ModelSettings.from_dict({"recency_lambda": 0.03, "recency_half_life_days": 30})
    assert s2.recency_lambda == 0.03
