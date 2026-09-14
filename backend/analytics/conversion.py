"""Сглаженная вероятность продажи (Bayesian shrinkage)."""

from __future__ import annotations


def smoothed_conversion(
    successes: float,
    trials: float,
    global_conversion: float,
    prior_strength: float,
) -> float:
    """
    adjusted_conversion =
      (successes + prior_strength * global_conversion)
      / (trials + prior_strength)

    Сглаженная конверсия снижает влияние случайных результатов.
    Если менеджер провёл всего 2 переговоров, система не считает результат
    2 из 2 доказательством стабильного преимущества.
    """
    if prior_strength < 0:
        raise ValueError("prior_strength must be >= 0")
    if trials < 0 or successes < 0:
        raise ValueError("successes/trials must be >= 0")
    if successes > trials + 1e-9:
        raise ValueError("successes cannot exceed trials")
    global_conversion = min(1.0, max(0.0, float(global_conversion)))
    denom = trials + prior_strength
    if denom <= 0:
        return global_conversion
    return (successes + prior_strength * global_conversion) / denom


def raw_conversion(successes: float, trials: float) -> float | None:
    if trials <= 0:
        return None
    return successes / trials
