"""In-memory состояние демо-приложения."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from analytics.config import MANAGERS, ModelSettings
from data.generator import generate_demo_bundle
from optimization.pipeline import build_recommendations
from optimization.simulation import run_simulation


class AppState:
    def __init__(self) -> None:
        self.settings = ModelSettings()
        self.history: pd.DataFrame = pd.DataFrame()
        self.applications: pd.DataFrame = pd.DataFrame()
        self.scenario: str = "normal"
        self.scenario_label: str = ""
        self.seed: int = 42
        self.as_of: str = ""
        self.disclaimer: str = ""
        self.result: dict[str, Any] | None = None
        self.overrides: dict[str, dict[str, Any]] = {}
        self.mode: str = "demo"  # demo | analysis
        self.generate_day(seed=42, scenario="normal")

    def generate_day(self, seed: int = 42, scenario: str = "normal") -> dict[str, Any]:
        bundle = generate_demo_bundle(
            seed=seed,
            scenario=scenario,
            applications_per_day=self.settings.applications_per_day,
        )
        self.history = bundle["history"]
        self.applications = bundle["applications"]
        self.scenario = bundle["scenario"]
        self.scenario_label = bundle["scenario_label"]
        self.seed = bundle["seed"]
        self.as_of = bundle["as_of"]
        self.disclaimer = bundle["disclaimer"]
        self.settings.demo_seed = seed
        self.settings.manager_capacities = dict(bundle["manager_capacities"])
        # усечём team capacity если сумма индивидуальных меньше
        total_slots = sum(self.settings.manager_capacities.values())
        self.settings.team_capacity = min(50, total_slots) if scenario != "capacity_tight" else min(50, total_slots)
        if scenario == "capacity_tight":
            self.settings.team_capacity = 50
        self.overrides = {}
        self.mode = "demo"
        self.recalculate()
        return {"ok": True, "scenario": self.scenario, "seed": self.seed}

    def recalculate(self) -> dict[str, Any]:
        self.result = build_recommendations(
            self.history,
            self.applications,
            self.settings,
            seed=self.seed,
        )
        # всегда фиксируем системную рекомендацию до manual override
        if self.result:
            for rec in self.result["recommendations"]:
                if rec.get("recommended_manager"):
                    rec["system_recommended_manager"] = rec["recommended_manager"]
                    rec["system_expected_gm"] = rec["expected_gm"]
                    rec["original_recommendation"] = {
                        "manager": rec["recommended_manager"],
                        "expected_gm": rec["expected_gm"],
                    }

        # применить overrides с сохранением исходной рекомендации и без нарушения capacity
        if self.overrides and self.result:
            load: dict[str, int] = {m: 0 for m in MANAGERS}
            for rec in self.result["recommendations"]:
                if rec["selected"] and rec.get("recommended_manager"):
                    load[rec["recommended_manager"]] = load.get(rec["recommended_manager"], 0) + 1

            for app_id, ov in list(self.overrides.items()):
                rec = next((r for r in self.result["recommendations"] if r["application_id"] == app_id), None)
                if not rec or not rec["selected"]:
                    continue
                original = rec.get("system_recommended_manager") or rec["recommended_manager"]
                new_m = ov["manager"]
                if new_m == original:
                    rec["override"] = {
                        **ov,
                        "original_manager": original,
                        "original_expected_gm": rec.get("system_expected_gm", rec["expected_gm"]),
                        "manual_manager": new_m,
                    }
                    continue

                # освобождаем слот original, проверяем capacity нового
                caps = self.settings.manager_capacities
                load[original] = max(0, load.get(original, 0) - 1)
                if load.get(new_m, 0) >= caps.get(new_m, 0):
                    # откат: не применяем нарушение
                    load[original] = load.get(original, 0) + 1
                    ov = {
                        **ov,
                        "rejected": True,
                        "reject_reason": (
                            f"Нельзя назначить заявку этому менеджеру: "
                            f"достигнута его дневная capacity ({caps.get(new_m, 0)})."
                        ),
                        "original_manager": original,
                        "original_expected_gm": rec.get("system_expected_gm", rec["expected_gm"]),
                        "manual_manager": new_m,
                    }
                    self.overrides[app_id] = ov
                    rec["override"] = ov
                    continue

                load[new_m] = load.get(new_m, 0) + 1
                orig_gm = rec.get("system_expected_gm", rec["expected_gm"])
                rec["recommended_manager"] = new_m
                for s in rec["all_manager_scores"]:
                    if s["manager"] == new_m:
                        rec["expected_gm"] = s["expected_gm"]
                        rec["p_sale"] = s["p_sale"]
                        rec["confidence"] = s["confidence"]
                        rec["confidence_label"] = s["confidence_label"]
                        break
                rec["override"] = {
                    **ov,
                    "rejected": False,
                    "original_manager": original,
                    "original_expected_gm": orig_gm,
                    "manual_manager": new_m,
                    "timestamp": ov.get("timestamp"),
                }

            total = 0.0
            for rec in self.result["recommendations"]:
                if rec["selected"] and rec.get("recommended_manager"):
                    total += float(rec["expected_gm"])
            self.result["manager_load"] = load
            self.result["kpi"]["expected_gm"] = round(total, 2)
            n = self.result["kpi"]["recommended"]
            self.result["kpi"]["avg_gm_per_talk"] = round(total / n, 2) if n else 0
        return self.result

    def update_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        current = self.settings.to_dict()
        current.update(data)
        self.settings = ModelSettings.from_dict(current)
        self.recalculate()
        return self.settings.to_dict()

    def override(self, application_id: str, manager: str, reason: str, comment: str = "") -> dict[str, Any]:
        from datetime import datetime, timezone

        if self.result is None:
            self.recalculate()
        assert self.result is not None

        rec = next((r for r in self.result["recommendations"] if r["application_id"] == application_id), None)
        if rec is None:
            raise ValueError("Заявка не найдена")
        if not rec.get("selected"):
            raise ValueError("Можно изменить менеджера только у выбранной к обработке заявки")

        # load без текущей заявки (учитываем уже применённые успешные overrides)
        load: dict[str, int] = {m: 0 for m in MANAGERS}
        for r in self.result["recommendations"]:
            if not r["selected"] or r["application_id"] == application_id:
                continue
            m = r.get("recommended_manager")
            load[m] = load.get(m, 0) + 1

        current_m = rec.get("recommended_manager")
        caps = self.settings.manager_capacities
        if manager != current_m and load.get(manager, 0) >= int(caps.get(manager, 0)):
            raise ValueError(
                f"Нельзя назначить заявку этому менеджеру: достигнута его дневная capacity ({caps.get(manager, 0)})."
            )

        original = rec.get("system_recommended_manager") or rec.get("recommended_manager")
        self.overrides[application_id] = {
            "manager": manager,
            "reason": reason,
            "comment": comment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_manager": original,
        }
        self.recalculate()
        applied = self.overrides.get(application_id, {})
        if applied.get("rejected"):
            raise ValueError(applied.get("reject_reason") or "Нельзя назначить: capacity исчерпана.")
        return applied

    def get_dashboard(self) -> dict[str, Any]:
        assert self.result is not None
        return {
            "kpi": self.result["kpi"],
            "charts": self.result["charts"],
            "manager_load": self.result["manager_load"],
            "disclaimer": self.result["disclaimer"],
            "core_idea": self.result["core_idea"],
            "scenario": self.scenario,
            "scenario_label": self.scenario_label,
            "seed": self.seed,
            "as_of": self.as_of,
            "mode": self.mode,
            "timestamp": self.result["timestamp"],
        }

    def simulation(self, days: int = 14, auto_share: float = 0.5) -> dict[str, Any]:
        return run_simulation(days=days, auto_share=auto_share, seed=self.seed, settings=self.settings)

    def load_analysis_data(self, history: pd.DataFrame, applications: pd.DataFrame) -> None:
        self.history = history
        self.applications = applications
        self.mode = "analysis"
        self.scenario = "imported"
        self.scenario_label = "Загруженные данные"
        self.disclaimer = "Данные загружены пользователем. Проверьте качество и полноту полей."
        self.overrides = {}
        self.recalculate()


STATE = AppState()
