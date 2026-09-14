"""Оценка пар заявка × менеджер с fallback hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from analytics.confidence import (
    FALLBACK_LABELS_RU,
    FALLBACK_ORDER,
    FallbackLevel,
    confidence_label,
    confidence_score,
)
from analytics.config import ModelSettings
from analytics.conversion import raw_conversion, smoothed_conversion
from analytics.gm_model import ExpectedGMBreakdown, expected_gm
from analytics.recency import recency_weight, to_date


@dataclass
class PairScore:
    application_id: str
    manager: str
    region: str
    product: str
    p_sale: float
    raw_p_sale: float | None
    expected_check: float
    expected_gm_pct: float
    expected_gm: float
    expected_gm_per_sale: float
    confidence: float
    confidence_label: str
    n_observations: float
    n_successes: float
    fallback_level: str
    fallback_label: str
    avg_discount: float | None
    used_fallback: bool
    priority: float
    breakdown: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _match_mask(df: pd.DataFrame, level: FallbackLevel, manager: str, region: str, product: str) -> pd.Series:
    if level == FallbackLevel.MANAGER_REGION_PRODUCT:
        return (df["manager"] == manager) & (df["region"] == region) & (df["product"] == product)
    if level == FallbackLevel.MANAGER_REGION:
        return (df["manager"] == manager) & (df["region"] == region)
    if level == FallbackLevel.MANAGER_PRODUCT:
        return (df["manager"] == manager) & (df["product"] == product)
    if level == FallbackLevel.MANAGER:
        return df["manager"] == manager
    if level == FallbackLevel.REGION_PRODUCT:
        return (df["region"] == region) & (df["product"] == product)
    return pd.Series(True, index=df.index)


def _weighted_stats(
    subset: pd.DataFrame,
    as_of: date,
    lambda_: float,
    prior_strength: float,
    global_p: float,
    global_gm_sale: float,
    global_check: float,
    global_gm_pct: float,
) -> dict[str, float]:
    if subset.empty:
        return {
            "trials": 0.0,
            "successes": 0.0,
            "raw_p": None,  # type: ignore
            "p": smoothed_conversion(0, 0, global_p, prior_strength),
            "gm_per_sale": global_gm_sale,
            "check": global_check,
            "gm_pct": global_gm_pct,
            "discount": float("nan"),
        }

    weights = subset["date"].apply(lambda d: recency_weight(d, as_of, lambda_)).astype(float)
    trials = float(weights.sum())
    successes = float((weights * subset["sale"].astype(float)).sum())
    raw_p = raw_conversion(successes, trials)
    p = smoothed_conversion(successes, trials, global_p, prior_strength)

    sold = subset[subset["sale"] == 1]
    if sold.empty:
        gm_per_sale = global_gm_sale
        check = global_check
        gm_pct = global_gm_pct
        discount = float("nan")
    else:
        sw = sold["date"].apply(lambda d: recency_weight(d, as_of, lambda_)).astype(float)
        sw_sum = float(sw.sum()) or 1.0
        gm_per_sale = float((sw * sold["gm"].astype(float)).sum() / sw_sum)
        check = float((sw * sold["sale_amount"].astype(float)).sum() / sw_sum)
        # gm% = gm / sale_amount
        pcts = sold["gm"].astype(float) / sold["sale_amount"].astype(float).clip(lower=1.0)
        gm_pct = float((sw * pcts).sum() / sw_sum)
        if "discount" in sold.columns:
            discount = float((sw * sold["discount"].astype(float)).sum() / sw_sum)
        else:
            discount = float("nan")

    return {
        "trials": trials,
        "successes": successes,
        "raw_p": raw_p,
        "p": p,
        "gm_per_sale": max(0.0, gm_per_sale),
        "check": max(0.0, check),
        "gm_pct": min(1.0, max(0.0, gm_pct)),
        "discount": discount,
    }


def historical_data(history: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """
    Единая защита от data leakage: для решения на as_of доступна только история
    со строго более ранней датой (решение принимается в начале дня as_of).
    """
    if history is None or len(history) == 0:
        return history.copy() if isinstance(history, pd.DataFrame) else pd.DataFrame()
    hist = history.copy()
    hist["date"] = pd.to_datetime(hist["date"]).dt.date
    as_of_d = to_date(as_of)
    return hist.loc[hist["date"] < as_of_d].copy()


def compute_global_priors(history: pd.DataFrame, as_of: date, lambda_: float) -> dict[str, float]:
    # history already expected to be leakage-filtered by callers; filter again defensively
    history = historical_data(history, as_of) if len(history) and "date" in history.columns else history
    if history.empty:
        return {"p": 0.25, "gm_sale": 250.0, "check": 800.0, "gm_pct": 0.3}
    w = history["date"].apply(lambda d: recency_weight(d, as_of, lambda_)).astype(float)
    trials = float(w.sum()) or 1.0
    successes = float((w * history["sale"].astype(float)).sum())
    p = successes / trials
    sold = history[history["sale"] == 1]
    if sold.empty:
        return {"p": p, "gm_sale": 250.0, "check": 800.0, "gm_pct": 0.3}
    sw = sold["date"].apply(lambda d: recency_weight(d, as_of, lambda_)).astype(float)
    sw_sum = float(sw.sum()) or 1.0
    gm_sale = float((sw * sold["gm"].astype(float)).sum() / sw_sum)
    check = float((sw * sold["sale_amount"].astype(float)).sum() / sw_sum)
    pcts = sold["gm"].astype(float) / sold["sale_amount"].astype(float).clip(lower=1.0)
    gm_pct = float((sw * pcts).sum() / sw_sum)
    return {"p": p, "gm_sale": gm_sale, "check": check, "gm_pct": gm_pct}


def score_pair(
    history: pd.DataFrame,
    application: dict[str, Any],
    manager: str,
    settings: ModelSettings,
    as_of: date | None = None,
    globals_: dict[str, float] | None = None,
) -> PairScore:
    as_of = as_of or to_date(application.get("date"))
    region = application["region"]
    product = application["product"]
    app_id = str(application["application_id"])

    hist = historical_data(history, as_of)

    if globals_ is None:
        globals_ = compute_global_priors(hist, as_of, settings.recency_lambda)

    chosen_level = FallbackLevel.GLOBAL
    stats = None
    for level in FALLBACK_ORDER:
        mask = _match_mask(hist, level, manager, region, product)
        subset = hist.loc[mask]
        # Переходим на более общий уровень, если наблюдений мало
        if level != FallbackLevel.GLOBAL and len(subset) < settings.min_observations:
            continue
        stats = _weighted_stats(
            subset,
            as_of,
            settings.recency_lambda,
            settings.prior_strength,
            globals_["p"],
            globals_["gm_sale"],
            globals_["check"],
            globals_["gm_pct"],
        )
        chosen_level = level
        break

    if stats is None:
        stats = _weighted_stats(
            hist,
            as_of,
            settings.recency_lambda,
            settings.prior_strength,
            globals_["p"],
            globals_["gm_sale"],
            globals_["check"],
            globals_["gm_pct"],
        )
        chosen_level = FallbackLevel.GLOBAL

    egm = expected_gm(stats["p"], stats["gm_per_sale"])
    conf = confidence_score(stats["trials"], chosen_level, settings.min_observations)
    used_fallback = chosen_level != FallbackLevel.MANAGER_REGION_PRODUCT

    # Приоритет заявки для менеджера: ожидаемая GM × (0.5 + 0.5*confidence)
    priority = egm * (0.5 + 0.5 * conf)

    breakdown = ExpectedGMBreakdown(
        p_sale=stats["p"],
        expected_check=stats["check"],
        expected_gm_pct=stats["gm_pct"],
        expected_gm_per_sale=stats["gm_per_sale"],
        expected_gm=egm,
        raw_conversion=stats["raw_p"],
        smoothed_conversion=stats["p"],
        n_trials=stats["trials"],
        n_successes=stats["successes"],
        discount_avg=None if (stats["discount"] != stats["discount"]) else stats["discount"],
    )

    return PairScore(
        application_id=app_id,
        manager=manager,
        region=region,
        product=product,
        p_sale=round(stats["p"], 4),
        raw_p_sale=None if stats["raw_p"] is None else round(stats["raw_p"], 4),
        expected_check=round(stats["check"], 2),
        expected_gm_pct=round(stats["gm_pct"], 4),
        expected_gm=round(egm, 2),
        expected_gm_per_sale=round(stats["gm_per_sale"], 2),
        confidence=conf,
        confidence_label=confidence_label(conf),
        n_observations=round(stats["trials"], 2),
        n_successes=round(stats["successes"], 2),
        fallback_level=chosen_level.value,
        fallback_label=FALLBACK_LABELS_RU[chosen_level],
        avg_discount=None if breakdown.discount_avg is None else round(breakdown.discount_avg, 2),
        used_fallback=used_fallback,
        priority=round(priority, 2),
        breakdown={
            "steps": breakdown.as_formula_steps(),
            "raw_conversion": breakdown.raw_conversion,
            "smoothed_conversion": breakdown.smoothed_conversion,
        },
    )


def score_all_pairs(
    history: pd.DataFrame,
    applications: pd.DataFrame | list[dict],
    managers: list[str],
    settings: ModelSettings,
    as_of: date | None = None,
) -> list[PairScore]:
    if isinstance(applications, pd.DataFrame):
        apps = applications.to_dict(orient="records")
    else:
        apps = list(applications)
    if not apps:
        return []

    hist = historical_data(history, as_of or to_date(apps[0]["date"]))
    as_of = as_of or to_date(apps[0]["date"])
    globals_ = compute_global_priors(hist, as_of, settings.recency_lambda)

    scores: list[PairScore] = []
    for app in apps:
        for manager in managers:
            scores.append(score_pair(hist, app, manager, settings, as_of=as_of, globals_=globals_))
    return scores


def pairs_to_matrix(
    scores: list[PairScore],
    application_ids: list[str],
    managers: list[str],
) -> np.ndarray:
    idx = {a: i for i, a in enumerate(application_ids)}
    midx = {m: j for j, m in enumerate(managers)}
    mat = np.zeros((len(application_ids), len(managers)), dtype=float)
    for s in scores:
        mat[idx[s.application_id], midx[s.manager]] = s.expected_gm
    return mat
