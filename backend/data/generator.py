"""Генератор реалистичных синтетических данных для демо."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from analytics.config import MANAGERS, PRODUCTS, REGIONS


SCENARIOS = {
    "normal": "Нормальный день",
    "form_drop": "У одного менеджера резкое ухудшение текущей формы",
    "small_sample_hot": "Маленькая выборка с очень высоким показателем",
    "star_overloaded": "Очень сильный менеджер перегружен",
    "region_skew": "Большинство заявок на один регион",
    "product_skew": "Большинство заявок на один продукт",
    "capacity_tight": "Capacity почти полностью загружена",
}


# Базовые «истинные» силы менеджеров (для генерации, не для модели)
# conversion и gm uplift по (manager, region, product) — упрощённые профили
PROFILES = {
    "Менеджер 1": {"strength": {"офисные кресла": 1.25, "офисные столы": 1.0, "шкафы": 0.95}, "regions": {}},
    "Менеджер 2": {
        "strength": {"офисные кресла": 1.0, "офисные столы": 1.2, "шкафы": 0.95},
        "regions": {"Витебск": 1.15},
    },
    "Менеджер 3": {"strength": {"офисные кресла": 0.95, "офисные столы": 0.95, "шкафы": 1.3}, "regions": {}},
    "Менеджер 4": {
        "strength": {"офисные кресла": 1.05, "офисные столы": 1.1, "шкафы": 1.05},
        "regions": {"Гродно": 1.35},
    },
    "Менеджер 5": {"strength": {"офисные кресла": 1.0, "офисные столы": 1.0, "шкафы": 1.0}, "regions": {}},
}

BASE_CHECK = {
    "офисные кресла": 650,
    "офисные столы": 900,
    "шкафы": 1200,
}

BASE_GM_PCT = {
    "офисные кресла": 0.34,
    "офисные столы": 0.30,
    "шкафы": 0.28,
}


def _p_sale(manager: str, region: str, product: str, day_offset: int, scenario: str, rng: np.random.Generator) -> float:
    base = 0.28
    prof = PROFILES[manager]
    mult = prof["strength"].get(product, 1.0) * prof["regions"].get(region, 1.0)

    # временная динамика
    if manager == "Менеджер 4" and day_offset <= 21:
        # просадка в последние недели (и усиленная в сценарии form_drop)
        mult *= 0.72 if scenario == "form_drop" else 0.85
    if manager == "Менеджер 5" and day_offset <= 30:
        mult *= 1.18  # улучшился недавно

    if scenario == "small_sample_hot" and manager == "Менеджер 3" and product == "шкафы" and region == "Брест":
        # мало сделок, но удачные — добавим отдельно при генерации
        pass

    p = base * mult + rng.normal(0, 0.02)
    return float(np.clip(p, 0.05, 0.75))


def generate_history(
    seed: int = 42,
    days: int = 120,
    talks_per_day: int = 48,
    as_of: date | None = None,
    scenario: str = "normal",
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    as_of = as_of or date.today()
    rows: list[dict[str, Any]] = []
    deal_id = 1000

    for d in range(days, 0, -1):
        day = as_of - timedelta(days=d)
        n = talks_per_day + int(rng.integers(-5, 6))
        for _ in range(n):
            manager = str(rng.choice(MANAGERS))
            region = str(rng.choice(REGIONS))
            product = str(rng.choice(PRODUCTS))

            # сценарий: маленькая горячая выборка — редкие сделки М3/Брест/шкафы с высоким успехом
            if scenario == "small_sample_hot" and rng.random() < 0.01:
                manager, region, product = "Менеджер 3", "Брест", "шкафы"

            p = _p_sale(manager, region, product, d, scenario, rng)
            if scenario == "small_sample_hot" and manager == "Менеджер 3" and region == "Брест" and product == "шкафы":
                p = 0.92

            sale = 1 if rng.random() < p else 0
            discount = float(np.clip(rng.normal(0.08, 0.04), 0.0, 0.35))
            check = BASE_CHECK[product] * rng.uniform(0.75, 1.35) * (1 - discount * 0.5)
            gm_pct = BASE_GM_PCT[product] * rng.uniform(0.85, 1.15) * (1 - discount * 0.4)
            gm_pct = float(np.clip(gm_pct, 0.05, 0.55))
            sale_amount = round(check, 2) if sale else 0.0
            gm = round(sale_amount * gm_pct, 2) if sale else 0.0

            rows.append(
                {
                    "deal_id": deal_id,
                    "date": day.isoformat(),
                    "manager": manager,
                    "region": region,
                    "product": product,
                    "negotiations_held": 1,
                    "sale": sale,
                    "sale_amount": sale_amount,
                    "gm": gm,
                    "discount": round(discount, 3) if sale else 0.0,
                    "client_type": str(rng.choice(["новый", "повторный"], p=[0.7, 0.3])),
                    "source": str(rng.choice(["сайт", "звонок", "партнёр", "реклама"])),
                    "demo_data": True,
                }
            )
            deal_id += 1

    # Гарантируем пару «2 из 2» для демонстрации малой выборки
    if scenario in ("normal", "small_sample_hot"):
        for i in range(2):
            rows.append(
                {
                    "deal_id": deal_id + i,
                    "date": (as_of - timedelta(days=3 + i)).isoformat(),
                    "manager": "Менеджер 3",
                    "region": "Брест",
                    "product": "шкафы",
                    "negotiations_held": 1,
                    "sale": 1,
                    "sale_amount": 1400.0,
                    "gm": 420.0,
                    "discount": 0.05,
                    "client_type": "новый",
                    "source": "сайт",
                    "demo_data": True,
                }
            )

    df = pd.DataFrame(rows)
    return df


def generate_applications(
    seed: int = 42,
    n: int = 70,
    as_of: date | None = None,
    scenario: str = "normal",
) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 17)
    as_of = as_of or date.today()
    rows = []

    region_p = np.ones(len(REGIONS)) / len(REGIONS)
    product_p = np.ones(len(PRODUCTS)) / len(PRODUCTS)
    if scenario == "region_skew":
        region_p = np.array([0.55, 0.15, 0.1, 0.1, 0.1])
    if scenario == "product_skew":
        product_p = np.array([0.15, 0.15, 0.7])

    for i in range(n):
        region = str(rng.choice(REGIONS, p=region_p))
        product = str(rng.choice(PRODUCTS, p=product_p))
        urgency = str(rng.choice(["обычная", "высокая"], p=[0.8, 0.2]))
        rows.append(
            {
                "application_id": f"A{1000 + i}",
                "date": as_of.isoformat(),
                "region": region,
                "product": product,
                "source": str(rng.choice(["сайт", "звонок", "партнёр", "реклама"])),
                "client_type": str(rng.choice(["новый", "повторный"], p=[0.75, 0.25])),
                "urgency": urgency,
                "estimated_budget": round(float(BASE_CHECK[product] * rng.uniform(0.8, 1.4)), 2),
                "demo_data": True,
            }
        )
    return pd.DataFrame(rows)


def generate_demo_bundle(
    seed: int = 42,
    scenario: str = "normal",
    applications_per_day: int = 70,
    as_of: date | None = None,
) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        scenario = "normal"
    as_of = as_of or date.today()
    history = generate_history(seed=seed, as_of=as_of, scenario=scenario)
    applications = generate_applications(
        seed=seed, n=applications_per_day, as_of=as_of, scenario=scenario
    )
    manager_caps = {m: 10 for m in MANAGERS}
    if scenario == "star_overloaded":
        # сильный М4 почти без capacity
        manager_caps = {
            "Менеджер 1": 12,
            "Менеджер 2": 12,
            "Менеджер 3": 12,
            "Менеджер 4": 3,
            "Менеджер 5": 12,
        }
    if scenario == "capacity_tight":
        manager_caps = {m: 10 for m in MANAGERS}

    return {
        "history": history,
        "applications": applications,
        "scenario": scenario,
        "scenario_label": SCENARIOS[scenario],
        "as_of": as_of.isoformat(),
        "seed": seed,
        "manager_capacities": manager_caps,
        "disclaimer": "Демонстрационные данные для прототипа. Не являются реальными показателями компании.",
    }
