# LeadAssign fix report — 2026-09-13 / 2026-09-14

## BEFORE

| Defect | Behavior |
|--------|----------|
| **C1 DATA LEAKAGE** | `score_pair` / `score_all_pairs` использовали всю историю; будущие строки получали вес 1.0 через `max(0, days_old)` |
| **C2 OPTIMAL** | При `sum(caps) > team_capacity` proportional slot shrink → субоптимум (контрпример 320 vs 500) |
| **C3 OVERRIDE** | Не сохранялся `original_manager`; override мог превысить capacity (11/10) |

Документация завышала роль current form / confidence / urgency в optimal objective.

## AFTER

| Fix | Implementation |
|-----|----------------|
| **C1** | Единый `historical_data(history, as_of)` → `date < as_of`; применяется в scoring, baseline, form |
| **C2** | ILP PuLP/CBC: полные `capacity_m` + `team_capacity`; без proportional shrink |
| **C3** | `system_recommended_manager` / `original_manager` + capacity check; API 400 при отказе; UI показывает авто vs ручное |

## Mathematical validation

```text
algorithm optimum vs bruteforce (5 apps × 3 managers): MATCH
sum(caps)>team counterexample: optimal GM = 500 (all to M1)
```

## Tests

Regression suite (`tests/test_regression_c1_c2_c3.py` + existing):

- `test_future_rows_do_not_change_prediction`
- `test_no_future_leakage_only_future_history`
- `test_baseline_no_future_leakage`
- `test_optimal_assignment_respects_full_manager_caps`
- `test_team_capacity_less_than_sum_manager_caps`
- `test_optimal_assignment_matches_bruteforce_small_case`
- `test_manual_override_respects_capacity`
- `test_manual_override_preserves_original_recommendation`

Full pytest: **33 passed**.

## Verdict (post-fix audit)

```text
BUSINESS LOGIC: PASS
ASSIGNMENT OPTIMIZATION: PASS
70_TO_50_SELECTION: PASS
CAPACITY: PASS
EXPECTED_GM: PASS
SMALL_SAMPLE: PASS
FRESHNESS: PASS
DATA_LEAKAGE: PASS
FALLBACK: PASS
BASELINE: PASS
EXPLAINABILITY: PASS
MANUAL_OVERRIDE: PASS
TEST_COVERAGE: PASS
TEST_ASSIGNMENT_COMPLIANCE: PASS
```

`READY_TO_SHOW_EMPLOYER: YES`

## Honest limitations (not defects)

- Current form — explainability only
- Confidence — reliability / UI / tie-break, not ILP objective term
- Urgency — display priority only
- Expected GM models `P(sale|negotiation)`, not `P(negotiation)`

## Backup

`d:\тестовое_backup_2026-09-14_0002`
