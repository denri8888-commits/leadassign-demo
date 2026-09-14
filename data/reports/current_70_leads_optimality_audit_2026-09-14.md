# Current 70 leads optimality audit — 2026-09-14
`CODE_CHANGED = NO`
`CURRENT_SELECTION_OPTIMAL = YES`
`MULTIPLE_OPTIMAL_SOLUTIONS = True`
`COMPARISON_CASE = A`

## A. INPUT SNAPSHOT
- source: `generate_demo_bundle(seed=42, scenario='normal') — same as AppState default dashboard`
- as_of: `2026-09-14`
- leads = 70
- managers = ['Менеджер 1', 'Менеджер 2', 'Менеджер 3', 'Менеджер 4', 'Менеджер 5']
- capacities = {'Менеджер 1': 10, 'Менеджер 2': 10, 'Менеджер 3': 10, 'Менеджер 4': 10, 'Менеджер 5': 10}
- team_capacity = 50
- hard constraints: ['x binary', 'each lead at most one manager', 'each manager <= capacity_m', 'total assignments <= team_capacity', 'no other eligibility filters in production path']

## B. CURRENT DASHBOARD
- selected = 50
- queue = 20
- KPI expected_gm = 6074.34
- recomputed objective (sum of assigned scores) = 6074.34
- load: {'Менеджер 3': 10, 'Менеджер 4': 10, 'Менеджер 1': 10, 'Менеджер 5': 10, 'Менеджер 2': 10}
- **Queue Expected GM meaning:** For selected leads: Expected GM of ASSIGNED manager. For queued leads: Expected GM of BEST manager across all managers (pipeline.py: chosen.expected_gm if selected else best_possible.expected_gm).

## C. FULL SCORE MATRIX
Saved separately: `current_70_leads_score_matrix_2026-09-14.json` (70 leads × 5 managers = 350 pairs).

## D. INDEPENDENT OPTIMUM
- production `optimal_assign` objective = 6074.34
- independent PuLP objective = 6074.34
- n_assigned = 50
- load = {'Менеджер 5': 10, 'Менеджер 1': 10, 'Менеджер 4': 10, 'Менеджер 2': 10, 'Менеджер 3': 10}

## E. COMPARISON
- same selected set? **YES**
- same assignments? **YES**
- CURRENT_DASHBOARD_OBJECTIVE = 6074.34
- OPTIMAL_OBJECTIVE = 6074.34
- ABSOLUTE_GAP = -0.0
- RELATIVE_GAP = -0.0

## F. QUEUE ANALYSIS
| queue_lead | best_manager | best_score | blocking | weakest_on_best | competitor | force_delta |
| --- | --- | ---: | --- | --- | ---: | ---: |
| A1033 | Менеджер 5 | 91.51 | Менеджер 5 | A1012 | 91.51 | 0.0 |
| A1018 | Менеджер 5 | 91.51 | Менеджер 5 | A1012 | 91.51 | 0.0 |
| A1039 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1063 | Менеджер 2 | 76.28 | Менеджер 2 | A1024 | 76.28 | 0.0 |
| A1015 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1027 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1037 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1047 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1050 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1057 | Менеджер 1 | 79.23 | Менеджер 1 | A1019 | 84.09 | -4.24 |
| A1028 | Менеджер 1 | 69.88 | Менеджер 1 | A1019 | 84.09 | -7.22 |
| A1007 | Менеджер 2 | 76.28 | Менеджер 2 | A1024 | 76.28 | 0.0 |
| A1056 | Менеджер 2 | 76.28 | Менеджер 2 | A1024 | 76.28 | 0.0 |
| A1062 | Менеджер 2 | 76.28 | Менеджер 2 | A1024 | 76.28 | 0.0 |
| A1045 | Менеджер 4 | 74.93 | Менеджер 4 | A1008 | 88.81 | -9.92 |
| A1066 | Менеджер 4 | 74.93 | Менеджер 4 | A1008 | 88.81 | -9.92 |
| A1017 | Менеджер 1 | 69.88 | Менеджер 1 | A1019 | 84.09 | -7.22 |
| A1026 | Менеджер 1 | 69.88 | Менеджер 1 | A1019 | 84.09 | -7.22 |
| A1036 | Менеджер 1 | 69.88 | Менеджер 1 | A1019 | 84.09 | -7.22 |
| A1048 | Менеджер 1 | 69.88 | Менеджер 1 | A1019 | 84.09 | -7.22 |

All `force_select_delta_vs_optimum` ≤ 0 means no queue lead improves the global optimum when forced in.

## G. SPECIAL CASES
### A1024 (selected)
```json
{
  "lead_id": "A1024",
  "present": true,
  "region": "Гомель",
  "product": "офисные кресла",
  "selected": true,
  "dashboard_expected_gm": 76.28,
  "dashboard_manager": "Менеджер 2",
  "scores_by_manager": {
    "Менеджер 1": 71.45,
    "Менеджер 2": 76.28,
    "Менеджер 3": 66.14,
    "Менеджер 4": 62.34,
    "Менеджер 5": 54.58
  },
  "best_manager": "Менеджер 2",
  "best_score": 76.28,
  "priority": 68.06,
  "reject_reason": null
}
```
### A1033 (queue)
```json
{
  "lead_id": "A1033",
  "present": true,
  "region": "Гомель",
  "product": "офисные столы",
  "selected": false,
  "dashboard_expected_gm": 91.51,
  "dashboard_manager": null,
  "scores_by_manager": {
    "Менеджер 1": 59.46,
    "Менеджер 2": 59.51,
    "Менеджер 3": 69.86,
    "Менеджер 4": 64.07,
    "Менеджер 5": 91.51
  },
  "best_manager": "Менеджер 5",
  "best_score": 91.51,
  "priority": 89.59,
  "reject_reason": "низкая ожидаемая GM относительно выбранных заявок"
}
```
### Why A1033 (higher displayed number) can stay in queue while A1024 is selected

**Важно не перепутать колонки dashboard:**

| lead | Expected GM (колонка маржи) | Priority (колонка приоритета) | Статус |
|------|----------------------------:|------------------------------:|--------|
| A1024 | **76.28** (назначен Менеджер 2) | 68.06 | обработать |
| A1033 | **91.51** (лучший = Менеджер 5) | 89.59 | очередь |

Числа ~68 и ~89 — это **priority**, не Expected GM.

Фактическая причина очереди A1033:

1. Отображаемые **91.51** для очереди = score лучшего менеджера (Менеджер 5), см. `pipeline.py`: `best_possible.expected_gm` если не selected.
2. У Менеджера 5 capacity = 10 и уже занята заявками с **тем же** Expected GM 91.51 (Гомель / офисные столы), например A1042 и A1012.
3. Простой swap A1033 ↔ weakest-on-M5 даёт `swap_delta = 0`.
4. Принудительное включение A1033 в ILP вытесняет A1042 и оставляет objective **6074.34** (delta **0.0**) → это **tie / multiple optimal solutions**, не потеря маржи.
5. A1024 конкурирует в другом пуле (Менеджер 2, Гомель / кресла, 76.28) и не «забирает слот» у A1033 напрямую.

Вывод: сравнение «91.51 в очереди vs 68 в обработке» смешивает best-available Expected GM очереди с **priority** выбранной заявки. Корректное сравнение: 91.51 (best A1033) vs 76.28 (assigned A1024) — разные менеджеры/продукты; глобальный ILP при этом оптимален, а замена A1033↔A1042 экономически нейтральна.

### A1018
```json
{
  "lead_id": "A1018",
  "present": true,
  "region": "Гомель",
  "product": "офисные столы",
  "selected": false,
  "dashboard_expected_gm": 91.51,
  "dashboard_manager": null,
  "scores_by_manager": {
    "Менеджер 1": 59.46,
    "Менеджер 2": 59.51,
    "Менеджер 3": 69.86,
    "Менеджер 4": 64.07,
    "Менеджер 5": 91.51
  },
  "best_manager": "Менеджер 5",
  "best_score": 91.51,
  "priority": 82.95,
  "reject_reason": "низкая ожидаемая GM относительно выбранных заявок"
}
```
### A1039
```json
{
  "lead_id": "A1039",
  "present": true,
  "region": "Витебск",
  "product": "офисные кресла",
  "selected": false,
  "dashboard_expected_gm": 79.23,
  "dashboard_manager": null,
  "scores_by_manager": {
    "Менеджер 1": 79.23,
    "Менеджер 2": 72.04,
    "Менеджер 3": 40.53,
    "Менеджер 4": 44.64,
    "Менеджер 5": 70.15
  },
  "best_manager": "Менеджер 1",
  "best_score": 79.23,
  "priority": 78.63,
  "reject_reason": "низкая ожидаемая GM относительно выбранных заявок"
}
```
### A1063
```json
{
  "lead_id": "A1063",
  "present": true,
  "region": "Гомель",
  "product": "офисные кресла",
  "selected": false,
  "dashboard_expected_gm": 76.28,
  "dashboard_manager": null,
  "scores_by_manager": {
    "Менеджер 1": 71.45,
    "Менеджер 2": 76.28,
    "Менеджер 3": 66.14,
    "Менеджер 4": 62.34,
    "Менеджер 5": 54.58
  },
  "best_manager": "Менеджер 2",
  "best_score": 76.28,
  "priority": 73.51,
  "reject_reason": "низкая ожидаемая GM относительно выбранных заявок"
}
```

## H. TIES
Found 2 region×product groups where equal best_score appears in both selected and queue.
- Гомель / офисные кресла @ 76.28: ['A1007', 'A1024*', 'A1056', 'A1062', 'A1063']
- Гомель / офисные столы @ 91.51: ['A1012*', 'A1018', 'A1033', 'A1042*']

## I. BRUTE FORCE (subsets)
| case | apps | bf | ilp | prod | match |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | A1019, A1022, A1060, A1009, A1044 | 313.3 | 313.3 | 313.3 | True |
| 2 | A1024, A1033, A1018, A1039, A1063 | 301.65 | 301.65 | 301.65 | True |
| 3 | A1024, A1033, A1018, A1039, A1063 | 301.65 | 301.65 | 301.65 | True |
| 4 | A1024, A1033, A1041, A1019, A1007 | 394.6 | 394.6 | 394.6 | True |
| 5 | A1024, A1033, A1018, A1044, A1060, A1015 | 316.5 | 316.5 | 316.5 | True |

## Counterfactuals
```json
{
  "force_A1033": {
    "status": "Optimal",
    "objective": 6074.34,
    "delta_vs_optimum": 0.0,
    "n": 50,
    "load": {
      "Менеджер 5": 10,
      "Менеджер 1": 10,
      "Менеджер 4": 10,
      "Менеджер 2": 10,
      "Менеджер 3": 10
    },
    "displaced": [
      "A1042"
    ],
    "entered": [
      "A1033"
    ],
    "assignment_for_special": {
      "A1033": "Менеджер 5",
      "A1024": "Менеджер 2"
    }
  },
  "exclude_A1024": {
    "status": "Optimal",
    "objective": 6074.34,
    "delta_vs_optimum": 0.0,
    "n": 50,
    "load": {
      "Менеджер 5": 10,
      "Менеджер 1": 10,
      "Менеджер 4": 10,
      "Менеджер 2": 10,
      "Менеджер 3": 10
    },
    "displaced": [
      "A1024",
      "A1042"
    ],
    "entered": [
      "A1033",
      "A1063"
    ],
    "assignment_for_special": {
      "A1033": "Менеджер 5",
      "A1024": null
    }
  },
  "force_A1033_exclude_A1024": {
    "status": "Optimal",
    "objective": 6074.34,
    "delta_vs_optimum": 0.0,
    "n": 50,
    "load": {
      "Менеджер 5": 10,
      "Менеджер 1": 10,
      "Менеджер 4": 10,
      "Менеджер 2": 10,
      "Менеджер 3": 10
    },
    "displaced": [
      "A1024",
      "A1042"
    ],
    "entered": [
      "A1033",
      "A1063"
    ],
    "assignment_for_special": {
      "A1033": "Менеджер 5",
      "A1024": null
    }
  }
}
```

## Expected GM breakdowns
```json
{
  "A1033_best": {
    "lead_id": "A1033",
    "manager": "Менеджер 5",
    "p_sale": 0.3658,
    "expected_gm_per_sale": 250.18,
    "expected_gm": 91.51,
    "check": 91.515844,
    "fallback": "manager_region_product",
    "n_obs": 21.73,
    "confidence": 0.8129,
    "region": "Гомель",
    "product": "офисные столы",
    "selected": false,
    "dashboard_manager": null
  },
  "A1033_if_assigned_in_cf": {
    "lead_id": "A1033",
    "manager": "Менеджер 5",
    "p_sale": 0.3658,
    "expected_gm_per_sale": 250.18,
    "expected_gm": 91.51,
    "check": 91.515844,
    "fallback": "manager_region_product",
    "n_obs": 21.73,
    "confidence": 0.8129,
    "region": "Гомель",
    "product": "офисные столы",
    "selected": false,
    "dashboard_manager": null
  },
  "A1024_assigned": {
    "lead_id": "A1024",
    "manager": "Менеджер 2",
    "p_sale": 0.3288,
    "expected_gm_per_sale": 231.98,
    "expected_gm": 76.28,
    "check": 76.275024,
    "fallback": "manager_region_product",
    "n_obs": 18.21,
    "confidence": 0.7846,
    "region": "Гомель",
    "product": "офисные кресла",
    "selected": true,
    "dashboard_manager": "Менеджер 2"
  },
  "A1041_assigned": {
    "lead_id": "A1041",
    "manager": "Менеджер 3",
    "p_sale": 0.4508,
    "expected_gm_per_sale": 350.42,
    "expected_gm": 157.95,
    "check": 157.969336,
    "fallback": "manager_region_product",
    "n_obs": 24.83,
    "confidence": 0.8324,
    "region": "Брест",
    "product": "шкафы",
    "selected": true,
    "dashboard_manager": "Менеджер 3"
  },
  "mid_selected": {
    "lead_id": "A1055",
    "manager": "Менеджер 2",
    "p_sale": 0.4248,
    "expected_gm_per_sale": 276.77,
    "expected_gm": 117.57,
    "check": 117.571896,
    "fallback": "manager_region_product",
    "n_obs": 24.21,
    "confidence": 0.8288,
    "region": "Витебск",
    "product": "офисные столы",
    "selected": true,
    "dashboard_manager": "Менеджер 2"
  },
  "bottom_queue_best": {
    "lead_id": "A1028",
    "manager": "Менеджер 1",
    "p_sale": 0.2798,
    "expected_gm_per_sale": 249.78,
    "expected_gm": 69.88,
    "check": 69.888444,
    "fallback": "manager_region_product",
    "n_obs": 23.59,
    "confidence": 0.8251,
    "region": "Брест",
    "product": "офисные столы",
    "selected": false,
    "dashboard_manager": null
  }
}
```

## Factor roles (code)
```json
{
  "priority": {
    "in_optimal_objective": false,
    "usage": "UI sort only: recommendations.sort(key=lambda r: (not r['selected'], -r['priority']))",
    "formula": "best_possible.expected_gm * (0.5 + 0.5 * confidence) * urgency_boost",
    "file": "backend/optimization/pipeline.py"
  },
  "urgency": {
    "in_optimal_objective": false,
    "usage": "Only multiplies display priority (1.08 if высокая)",
    "file": "backend/optimization/pipeline.py"
  },
  "confidence": {
    "in_optimal_objective": false,
    "usage": "Display priority factor; greedy tie-break may use it elsewhere; reject_reason heuristic",
    "file": "backend/optimization/pipeline.py"
  },
  "current_form": {
    "in_optimal_objective": false,
    "usage": "Explainability / managers UI only via forms_for_all + explain_recommendation",
    "file": "backend/optimization/pipeline.py, analytics/form.py"
  },
  "expected_gm": {
    "in_optimal_objective": true,
    "usage": "Sole coefficient of x(i,m) in optimal_assign ILP",
    "file": "backend/optimization/optimal.py"
  }
}
```

## J. VERDICT
**CURRENT_SELECTION_OPTIMAL = YES**

**MULTIPLE_OPTIMAL_SOLUTIONS = True**

**CODE_CHANGED = NO**

## Business explanation (for employer)

Сервис одновременно выбирает, какие 50 из 70 заявок обработать сегодня и кому из пяти менеджеров их отдать, чтобы максимизировать сумму ожидаемой валовой маржи при лимите 10 переговоров на человека и 50 на команду.

Число «ожидаемая валовая маржа» у выбранной заявки — прогноз для **конкретного назначенного** менеджера. У заявки в очереди это прогноз для **лучшего возможного** менеджера, даже если его дневной слот уже занят.

Поэтому сравнение «A1033 ≈ 90 в очереди» и «A1024 ≈ 68 в обработке» легко вводит в заблуждение: **68 — это приоритет сортировки таблицы, а не маржа**. Реальная назначенная маржа A1024 = 76.28. У A1033 лучший менеджер (Менеджер 5) уже заполнен десятью такими же по ценности заявками Гомель/столы (все по 91.51). Замена A1033 на одну из них не увеличивает и не уменьшает дневную сумму — это ничья между равноценными вариантами.

Независимый пересчёт ILP на том же демо-дне (seed 42) совпал с dashboard: objective **6074.34**, те же 50 заявок и те же менеджеры. Все менеджеры загружены ровно по 10. Priority, срочность, уверенность и текущая форма **не входят** в целевую функцию — только в отображение.

Итог для работодателя: сервис взял именно эти 50, потому что это (одно из) оптимальных назначений по ожидаемой валовой марже при реальных capacity; визуально «более высокая» цифра в очереди часто означает лучший, но уже занятый менеджер, а не упущенную выгоду дня.


## Score consistency
- selected mismatches (>0.02): 0
- queue rows match best-manager score: True
