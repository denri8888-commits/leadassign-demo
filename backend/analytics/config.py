"""Константы и настройки модели по умолчанию."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Any


REGIONS = ["Витебск", "Могилёв", "Гомель", "Гродно", "Брест"]
PRODUCTS = ["офисные кресла", "офисные столы", "шкафы"]
MANAGERS = ["Менеджер 1", "Менеджер 2", "Менеджер 3", "Менеджер 4", "Менеджер 5"]

MANAGER_SHORT = {
    "Менеджер 1": "М1",
    "Менеджер 2": "М2",
    "Менеджер 3": "М3",
    "Менеджер 4": "М4",
    "Менеджер 5": "М5",
}

LN2 = math.log(2)


@dataclass
class ModelSettings:
    team_capacity: int = 50
    manager_capacities: dict[str, int] = field(
        default_factory=lambda: {m: 10 for m in MANAGERS}
    )
    # вес ≈ 0.5 примерно через half_life дней; λ = ln(2)/half_life
    # демо-default λ=0.03 сохранён (half_life ≈ 23.1 дня)
    recency_lambda: float = 0.03
    recency_half_life_days: float = round(LN2 / 0.03, 1)
    prior_strength: float = 8.0  # сила сглаживания малой выборки
    min_observations: int = 5
    extra_manager_monthly_cost: float = 3500.0  # демо-параметр, BYN
    working_days_per_month: int = 22
    form_recent_days: int = 30
    form_previous_days: int = 30
    form_short_days: int = 14
    form_long_days: int = 180
    form_dip_threshold: float = 0.15
    assignment_mode: str = "optimal"  # optimal | greedy
    currency: str = "BYN"
    demo_seed: int = 42
    applications_per_day: int = 70

    def apply_half_life(self, days: float) -> None:
        """Сделать период полураспада ведущим параметром свежести."""
        days = float(days)
        if days <= 0:
            raise ValueError("recency_half_life_days must be > 0")
        self.recency_half_life_days = round(days, 1)
        self.recency_lambda = round(LN2 / days, 6)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelSettings":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        if "manager_capacities" in filtered and filtered["manager_capacities"]:
            filtered["manager_capacities"] = dict(filtered["manager_capacities"])
        obj = cls(**filtered)
        # half-life ведущий только если λ не передали явно (иначе сохраняем λ для стабильности демо)
        if "recency_half_life_days" in data and "recency_lambda" not in data:
            obj.apply_half_life(float(obj.recency_half_life_days))
        elif obj.recency_lambda > 0:
            obj.recency_half_life_days = round(LN2 / float(obj.recency_lambda), 1)
        return obj

    def effective_slots(self) -> list[str]:
        """Список слотов переговоров, привязанных к менеджерам (≤ team_capacity)."""
        caps = {m: max(0, int(c)) for m, c in self.manager_capacities.items()}
        total = sum(caps.values())
        if total > self.team_capacity and total > 0:
            scaled = {m: int(caps[m] * self.team_capacity / total) for m in caps}
            while sum(scaled.values()) < self.team_capacity:
                m = max(caps, key=lambda x: caps[x] - scaled[x])
                scaled[m] += 1
            while sum(scaled.values()) > self.team_capacity:
                m = max(scaled, key=scaled.get)
                if scaled[m] > 0:
                    scaled[m] -= 1
                else:
                    break
            caps = scaled
        slots: list[str] = []
        for manager, cap in caps.items():
            slots.extend([manager] * cap)
        return slots


SETTING_HELPERS: dict[str, str] = {
    "team_capacity": "Максимум переговоров, которые команда может провести за день.",
    "manager_capacities": "Индивидуальный лимит переговоров на менеджера. Не обязан быть одинаковым.",
    "recency_half_life_days": (
        "Через сколько дней вес старой сделки становится примерно вдвое меньше. "
        "Например, около 23–30 дней. Внутри пересчитывается в коэффициент свежести."
    ),
    "recency_lambda": (
        "Технический коэффициент свежести. Удобнее менять период полураспада выше. "
        "Чем выше λ, тем сильнее доверие к последним неделям."
    ),
    "prior_strength": (
        "Сила сглаживания. Защищает от случайных результатов на маленькой выборке "
        "(например, 2 продажи из 2 переговоров ещё не означают 100%)."
    ),
    "min_observations": "Ниже этого числа наблюдений оценка считается менее надёжной и чаще берёт более общий уровень данных.",
    "extra_manager_monthly_cost": "Демонстрационный параметр. Реальное значение должно быть заменено финансовыми данными компании.",
    "working_days_per_month": "Используется в модуле экономики найма для перевода дневного эффекта в месячный.",
    "form_recent_days": "Соседнее окно формы для графика (обычно 30 дней).",
    "form_previous_days": "Предыдущее соседнее окно для сравнения на графике.",
    "form_short_days": "Короткое окно текущей формы (по умолчанию 14 дней).",
    "form_long_days": "Длинная база для сравнения формы (по умолчанию около 6 месяцев).",
    "form_dip_threshold": "Порог заметной просадки короткого окна относительно длинной базы (доля, например 0.15 = 15%).",
    "assignment_mode": "optimal — совместный выбор заявок и менеджеров; greedy — простой понятный алгоритм.",
    "applications_per_day": "Сколько заявок генерировать на демо-день (обычно 70).",
    "demo_seed": "Код воспроизводимости демо-данных.",
}
