"""Движок объяснений рекомендаций."""

from __future__ import annotations

from typing import Any

from analytics.scoring import PairScore


def explain_recommendation(
    chosen: PairScore,
    alternatives: list[PairScore],
    form: dict[str, Any] | None = None,
    capacity_ok: bool = True,
) -> dict[str, Any]:
    reasons: list[str] = []

    reasons.append(
        f"Ожидаемая вероятность продажи: {chosen.p_sale * 100:.1f}% "
        f"(сглаженная; по выборке: "
        f"{'нет данных' if chosen.raw_p_sale is None else f'{chosen.raw_p_sale * 100:.1f}%'})."
    )

    if not chosen.used_fallback:
        reasons.append(
            f"Хороший результат именно по «{chosen.product}» в регионе «{chosen.region}» "
            f"({chosen.n_observations:.0f} взвешенных наблюдений)."
        )
    else:
        reasons.append(
            f"Оценка построена по более общему уровню данных («{chosen.fallback_label}»), "
            "потому что по этому сочетанию мало истории."
        )

    if form:
        short_d = form.get("short_days", 14)
        long_d = form.get("long_days", 180)
        if form.get("dip_flag"):
            reasons.append(
                f"Замечена просадка формы: короткое окно ({short_d} дн.) слабее длинной базы "
                f"({long_d} дн.). В расчёте это уже учтено через больший вес свежей истории, "
                "без отдельного множителя."
            )
        elif form.get("direction") == "up":
            reasons.append(
                f"Недавние результаты выглядят сильнее обычного "
                f"(короткое окно {short_d} дн. vs база {long_d} дн.)."
            )
        elif form.get("direction") == "down":
            reasons.append(
                "Недавние результаты слабее обычного — свежая история уже имеет больший вес в оценке."
            )
        else:
            reasons.append("Текущая форма менеджера учтена через временное взвешивание истории.")

    if alternatives:
        best_alt = max(alternatives, key=lambda x: x.expected_gm)
        if chosen.expected_gm >= best_alt.expected_gm:
            reasons.append("Ожидаемая валовая маржа выше, чем у доступных альтернатив.")
        else:
            reasons.append(
                "Назначен с учётом лимитов загрузки; у альтернатив могла быть выше маржа, "
                "но свободные места заняты более выгодными заявками."
            )

    if capacity_ok:
        reasons.append("У менеджера есть свободное место в дневной загрузке.")

    if chosen.confidence_label == "низкая":
        reasons.append(
            f"Низкая уверенность: всего {chosen.n_observations:.0f} исторических наблюдений "
            f"на используемом уровне."
        )

    alt_rows = []
    ranked = sorted([chosen, *alternatives], key=lambda x: x.expected_gm, reverse=True)
    for i, s in enumerate(ranked[:5]):
        note = (
            "рекомендуем"
            if s.manager == chosen.manager
            else ("альтернатива" if i < 3 else "ниже ожидаемый результат")
        )
        alt_rows.append(
            {
                "manager": s.manager,
                "expected_gm": s.expected_gm,
                "confidence": s.confidence_label,
                "note": note,
                "p_sale": s.p_sale,
                "n_observations": s.n_observations,
            }
        )

    return {
        "application_id": chosen.application_id,
        "region": chosen.region,
        "product": chosen.product,
        "recommended_manager": chosen.manager,
        "reasons": reasons[:6],
        "alternatives": alt_rows,
        "formula": chosen.breakdown,
        "disclaimer": (
            "Это объяснение сформировано автоматически. "
            "Цифры — прогноз на демо-данных, а не гарантированная прибыль."
        ),
    }
