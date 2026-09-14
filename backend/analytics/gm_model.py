"""Модель ожидаемой валовой маржи."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExpectedGMBreakdown:
    p_sale: float
    expected_check: float
    expected_gm_pct: float
    expected_gm_per_sale: float
    expected_gm: float
    raw_conversion: float | None
    smoothed_conversion: float
    n_trials: float
    n_successes: float
    discount_avg: float | None

    def as_formula_steps(self) -> list[dict]:
        return [
            {"label": "Вероятность продажи", "value": self.smoothed_conversion, "format": "pct"},
            {"label": "Ожидаемый чек", "value": self.expected_check, "format": "money"},
            {"label": "Средняя валовая маржа", "value": self.expected_gm_pct, "format": "pct"},
            {"label": "Валовая маржа при успешной сделке", "value": self.expected_gm_per_sale, "format": "money"},
            {"label": "Сглаживание", "value": "учтено", "format": "text"},
            {"label": "Свежесть", "value": "учтена", "format": "text"},
            {"label": "Ожидаемая валовая маржа", "value": self.expected_gm, "format": "money"},
        ]


def expected_gm(p_sale: float, gm_per_successful_deal: float) -> float:
    """Expected GM = P(sale) × Expected GM per successful deal."""
    p = min(1.0, max(0.0, float(p_sale)))
    gm = max(0.0, float(gm_per_successful_deal))
    return p * gm


def expected_gm_from_check(p_sale: float, expected_check: float, gm_pct: float) -> float:
    """Expected GM = P(sale) × Expected sale amount × Expected GM %."""
    p = min(1.0, max(0.0, float(p_sale)))
    check = max(0.0, float(expected_check))
    pct = min(1.0, max(0.0, float(gm_pct)))
    return p * check * pct
