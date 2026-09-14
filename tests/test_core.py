"""Unit / scenario / integration tests for LeadAssign MVP."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from analytics.config import MANAGERS, ModelSettings
from analytics.confidence import FallbackLevel, confidence_score
from analytics.conversion import smoothed_conversion
from analytics.form import compute_manager_form
from analytics.gm_model import expected_gm
from analytics.recency import recency_weight
from analytics.scoring import score_all_pairs, score_pair
from data.generator import generate_applications, generate_demo_bundle, generate_history
from data.validation import validate_applications, validate_history
from optimization.baseline import baseline_best_historical, baseline_random
from optimization.greedy import greedy_assign
from optimization.optimal import optimal_assign
from optimization.pipeline import build_recommendations


def test_smoothed_conversion_shrinks_small_sample():
    raw = 1.0  # 2/2
    adj = smoothed_conversion(2, 2, global_conversion=0.3, prior_strength=8)
    assert adj < raw
    assert 0.3 < adj < 1.0


def test_recency_weight_decays():
    as_of = date(2026, 1, 30)
    w_new = recency_weight(date(2026, 1, 29), as_of, 0.05)
    w_old = recency_weight(date(2025, 10, 1), as_of, 0.05)
    assert w_new > w_old


def test_expected_gm_non_negative():
    assert expected_gm(0.4, 200) == 80
    assert expected_gm(-1, 100) == 0
    assert expected_gm(0.5, -10) == 0


def test_confidence_low_for_small_n():
    low = confidence_score(2, FallbackLevel.MANAGER_REGION_PRODUCT, min_observations=5)
    high = confidence_score(40, FallbackLevel.MANAGER_REGION_PRODUCT, min_observations=5)
    assert low < 0.4
    assert high > 0.7


def test_manager_with_2_of_2_not_automatically_best():
    as_of = date.today()
    rows = []
    for i in range(40):
        rows.append(
            {
                "date": (as_of - timedelta(days=i + 1)).isoformat(),
                "manager": "Менеджер 1",
                "region": "Брест",
                "product": "шкафы",
                "sale": 1 if i % 3 == 0 else 0,
                "sale_amount": 1200,
                "gm": 350 if i % 3 == 0 else 0,
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
                "gm": 500,
                "discount": 0.05,
            }
        )
    hist = pd.DataFrame(rows)
    # min_observations=1 позволяет взять узкий уровень 2/2 — но сглаживание режет 100%
    settings = ModelSettings(prior_strength=8, min_observations=1)
    app = {"application_id": "A1", "date": as_of.isoformat(), "region": "Брест", "product": "шкафы"}
    s3 = score_pair(hist, app, "Менеджер 3", settings, as_of=as_of)
    assert s3.raw_p_sale == pytest.approx(1.0, abs=1e-6)
    assert s3.p_sale < 0.95  # сглаживание уводит от 100%
    assert s3.p_sale == pytest.approx(
        smoothed_conversion(s3.n_successes, s3.n_observations, 0.3, 8), abs=0.15
    )

    # При стандартном min_observations система уходит в fallback, а не верит 2/2
    settings2 = ModelSettings(prior_strength=8, min_observations=5)
    s3b = score_pair(hist, app, "Менеджер 3", settings2, as_of=as_of)
    assert s3b.used_fallback is True
    assert s3b.confidence_label in ("низкая", "средняя", "высокая")


def test_form_drop_affects_recent_metric():
    as_of = date.today()
    rows = []
    for i in range(1, 61):
        sale = 1 if i > 30 else 0  # недавно хуже: i=1..30 recent window
        # recent = last 30 days: i=1..30 all sale=0; previous i=31..60 all sale=1
        rows.append(
            {
                "date": (as_of - timedelta(days=i)).isoformat(),
                "manager": "Менеджер 4",
                "region": "Гродно",
                "product": "офисные столы",
                "sale": 0 if i <= 30 else 1,
                "sale_amount": 900 if i > 30 else 0,
                "gm": 270 if i > 30 else 0,
            }
        )
    hist = pd.DataFrame(rows)
    form = compute_manager_form(hist, "Менеджер 4", as_of, recent_days=30, previous_days=30, min_observations=5)
    assert form.recent_metric < form.previous_metric
    assert form.direction in ("down", "flat", "unknown")


def test_capacity_not_exceeded_and_one_manager_per_app():
    bundle = generate_demo_bundle(seed=7, scenario="normal")
    settings = ModelSettings(team_capacity=50, manager_capacities={m: 10 for m in MANAGERS})
    result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=7)
    assert result["kpi"]["recommended"] <= 50
    assert result["kpi"]["recommended"] == 50
    apps = [r["application_id"] for r in result["recommendations"] if r["selected"]]
    assert len(apps) == len(set(apps))
    for m, load in result["manager_load"].items():
        assert load <= settings.manager_capacities[m]


def test_overloaded_manager_not_infinite():
    bundle = generate_demo_bundle(seed=11, scenario="star_overloaded")
    settings = ModelSettings(
        team_capacity=50,
        manager_capacities=bundle["manager_capacities"],
    )
    result = build_recommendations(bundle["history"], bundle["applications"], settings, seed=11)
    assert result["manager_load"].get("Менеджер 4", 0) <= bundle["manager_capacities"]["Менеджер 4"]


def test_low_confidence_when_sparse():
    as_of = date.today()
    hist = pd.DataFrame(
        [
            {
                "date": (as_of - timedelta(days=2)).isoformat(),
                "manager": "Менеджер 2",
                "region": "Гомель",
                "product": "офисные кресла",
                "sale": 1,
                "sale_amount": 700,
                "gm": 200,
                "discount": 0.1,
            }
        ]
    )
    # add some global data so priors exist
    extra = generate_history(seed=1, days=30, talks_per_day=20, as_of=as_of)
    hist = pd.concat([hist, extra], ignore_index=True)
    settings = ModelSettings(min_observations=5, prior_strength=8)
    app = {"application_id": "X", "date": as_of.isoformat(), "region": "Гомель", "product": "офисные кресла"}
    s = score_pair(hist, app, "Менеджер 2", settings, as_of=as_of)
    assert s.confidence_label in ("низкая", "средняя", "высокая")
    # For very specific combo with few obs, either fallback or low confidence
    assert s.used_fallback or s.confidence < 0.7


def test_no_data_leakage_in_applications():
    apps = generate_applications(seed=3, n=70)
    forbidden = {"sale", "gm", "discount", "sale_amount"}
    assert forbidden.isdisjoint(set(apps.columns))


def test_validation_rejects_negative_amounts():
    df = pd.DataFrame(
        [
            {
                "date": "2026-01-01",
                "manager": "Менеджер 1",
                "region": "Брест",
                "product": "шкафы",
                "sale": 1,
                "sale_amount": -10,
                "gm": 1,
            }
        ]
    )
    errors = validate_history(df)
    assert any("Отрицательная" in e for e in errors)


def test_greedy_and_optimal_respect_team_cap():
    bundle = generate_demo_bundle(seed=5)
    settings = ModelSettings()
    scores = score_all_pairs(bundle["history"], bundle["applications"], MANAGERS, settings)
    ids = [str(x) for x in bundle["applications"]["application_id"]]
    g = greedy_assign(scores, 50, settings.manager_capacities)
    o = optimal_assign(scores, ids, 50, settings.manager_capacities)
    assert g["n_assigned"] <= 50
    assert o["n_assigned"] <= 50


def test_baselines_run():
    bundle = generate_demo_bundle(seed=9)
    settings = ModelSettings()
    scores = score_all_pairs(bundle["history"], bundle["applications"], MANAGERS, settings)
    ids = [str(x) for x in bundle["applications"]["application_id"]]
    r = baseline_random(ids, MANAGERS, scores, 50, settings.manager_capacities, seed=1)
    m = baseline_best_historical(bundle["history"], bundle["applications"], MANAGERS, scores, settings)
    assert r["n_assigned"] > 0 and m["n_assigned"] > 0


def test_duplicate_application_ids_detected():
    df = pd.DataFrame(
        [
            {"application_id": "A1", "date": "2026-01-01", "region": "Брест", "product": "шкафы"},
            {"application_id": "A1", "date": "2026-01-01", "region": "Гродно", "product": "шкафы"},
        ]
    )
    assert any("Дубликат" in e for e in validate_applications(df))


@pytest.mark.parametrize("n_apps,n_managers", [(70, 5), (200, 10)])
def test_scoring_performance_smoke(n_apps, n_managers):
    import time

    as_of = date.today()
    hist = generate_history(seed=2, days=60, talks_per_day=40, as_of=as_of)
    apps = generate_applications(seed=2, n=n_apps, as_of=as_of)
    managers = MANAGERS[: min(5, n_managers)] if n_managers <= 5 else MANAGERS
    # for larger manager count reuse names with suffix conceptually — keep 5 for realism
    settings = ModelSettings()
    t0 = time.perf_counter()
    scores = score_all_pairs(hist, apps, managers, settings, as_of=as_of)
    elapsed = time.perf_counter() - t0
    assert len(scores) == n_apps * len(managers)
    assert elapsed < 15.0  # should be near-instant for 70×5; allow headroom


def test_api_health():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    dash = client.get("/api/dashboard")
    assert dash.status_code == 200
    body = dash.json()
    assert body["kpi"]["total_applications"] == 70
    assert body["kpi"]["recommended"] <= 50
    apps = client.get("/api/applications")
    assert apps.status_code == 200
    assert len(apps.json()["items"]) == 70
