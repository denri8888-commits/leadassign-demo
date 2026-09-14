"""Дополнительные тесты: data leakage и health."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from app.main import app
from data.generator import generate_applications


def test_health_has_demo_flag():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert "version" in body


def test_new_applications_have_no_outcome_fields():
    apps = generate_applications(seed=99, n=70)
    leak_cols = {"sale", "gm", "discount", "sale_amount", "negotiations_held"}
    assert leak_cols.isdisjoint(set(apps.columns))


def test_recommendation_payload_does_not_include_future_outcomes():
    client = TestClient(app)
    items = client.get("/api/applications").json()["items"]
    assert len(items) == 70
    for row in items[:10]:
        assert "sale" not in row or row.get("sale") is None
        # expected fields are forecasts, not realized outcomes for the new lead
        assert "expected_gm" in row
        assert "p_sale" in row
