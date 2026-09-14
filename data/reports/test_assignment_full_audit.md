# Full audit (post C1–C3) — LeadAssign

Дата: 2026-09-14 (отчёт датирован 2026-09-13 по запросу фикса).

Подробности исправлений: `test_assignment_fix_2026-09-13.md` / `.json`.

## Verdict

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

READY_TO_SHOW_EMPLOYER: YES

## Ключевые проверки

| Scenario | Result |
|----------|--------|
| 70→50 | PASS |
| 40/50, 50/50, 100/50 | PASS |
| Unequal caps + M5=0 | PASS |
| Greedy counterexample | Optimal 197 |
| sum(caps)>team | Optimal 500 (all M1) |
| Brute-force small ILP | MATCH |
| Future leakage | 0 changed pairs |
| Manual override capacity | Reject 400 |
| Original recommendation preserved | PASS |

## Честные ограничения MVP

- current form — explainability only
- confidence — не в ILP objective
- urgency — только display priority
- Expected GM = P(sale\|negotiation) × E[GM\|sale]
