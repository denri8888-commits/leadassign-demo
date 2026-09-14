"""Уверенность оценки и уровни fallback."""

from __future__ import annotations

from enum import Enum


class FallbackLevel(str, Enum):
    MANAGER_REGION_PRODUCT = "manager_region_product"
    MANAGER_REGION = "manager_region"
    MANAGER_PRODUCT = "manager_product"
    MANAGER = "manager"
    REGION_PRODUCT = "region_product"
    GLOBAL = "global"


FALLBACK_ORDER = [
    FallbackLevel.MANAGER_REGION_PRODUCT,
    FallbackLevel.MANAGER_REGION,
    FallbackLevel.MANAGER_PRODUCT,
    FallbackLevel.MANAGER,
    FallbackLevel.REGION_PRODUCT,
    FallbackLevel.GLOBAL,
]

FALLBACK_LABELS_RU = {
    FallbackLevel.MANAGER_REGION_PRODUCT: "менеджер + регион + продукт",
    FallbackLevel.MANAGER_REGION: "менеджер + регион",
    FallbackLevel.MANAGER_PRODUCT: "менеджер + продукт",
    FallbackLevel.MANAGER: "менеджер",
    FallbackLevel.REGION_PRODUCT: "регион + продукт",
    FallbackLevel.GLOBAL: "общая статистика",
}

# Базовый коэффициент уверенности по уровню (дальше умножается на объём выборки)
LEVEL_CONFIDENCE = {
    FallbackLevel.MANAGER_REGION_PRODUCT: 1.0,
    FallbackLevel.MANAGER_REGION: 0.85,
    FallbackLevel.MANAGER_PRODUCT: 0.85,
    FallbackLevel.MANAGER: 0.7,
    FallbackLevel.REGION_PRODUCT: 0.55,
    FallbackLevel.GLOBAL: 0.4,
}


def confidence_score(
    n_observations: float,
    level: FallbackLevel,
    min_observations: int = 5,
) -> float:
    """
    Уверенность в [0, 1].
    Мало наблюдений → низкая уверенность; более общий fallback → ещё ниже.
    """
    n = max(0.0, float(n_observations))
    sample_factor = n / (n + min_observations)
    return round(min(1.0, sample_factor * LEVEL_CONFIDENCE[level]), 4)


def confidence_label(score: float) -> str:
    if score >= 0.7:
        return "высокая"
    if score >= 0.4:
        return "средняя"
    return "низкая"
