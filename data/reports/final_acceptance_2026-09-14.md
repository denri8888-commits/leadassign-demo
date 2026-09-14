# Final acceptance — 2026-09-14

Acceptance-аудит готового LeadAssign **без изменения кода**.  
Проверен пакет: `LeadAssign_Nemetskie_Okna_Bel_FINAL_2026-09-13.zip`.

Распаковка: `d:\LeadAssign_ACCEPTANCE_2026-09-14`.

---

## Technical

| Check | Result |
|-------|--------|
| pytest | **33 passed**, 0 failed |
| full audit (`scripts/run_full_audit.py`) | all verdicts **PASS**, READY=YES |
| data leakage | future rows do not change scores |
| ILP / sum(caps)>team | counterexample → 500 (all to M1) |
| brute-force small case | algorithm = optimum |
| capacity invariants | 70/50/20, unequal caps, M5=0 |
| manual override | reject when full; original preserved |

## Product

| Area | Result | Notes |
|------|--------|-------|
| Dashboard 70/50/20 | **PASS** | KPI + «Не вошли в загрузку» = 20 |
| Recommendations table | **PASS** | region, product, manager, expected GM label, confidence |
| Explainability | **PASS** | reasons, alternatives, formula, n_obs, fallback label |
| Queue of 20 | **PASS** | all have `reject_reason` (heuristic, not shadow price) |
| Manual override UI/API | **PASS** | original vs manual; capacity error text |
| Baseline KPIs | **PASS** | random / manual / greedy / optimal |
| Capacity simulator | **PASS** | `/api/capacity` + UI «Анализ загрузки» |
| Effect simulation | **PASS** | `/api/simulation` |
| Import routes | **PASS** | `/api/import/preview`, `/api/import/apply` present |
| UI terminology | **PARTIAL** | main labels use «валовая маржа» / «уверенность»; residual «GM» in reject/explanation strings |

### Соответствие `docs/test_task_answer.md`

| Тезис | Verdict |
|-------|---------|
| 70 заявок / capacity 50 / очередь 20 | PASS |
| Выбор лучших назначений (не «взять любые 50») | PASS |
| менеджер × регион × продукт | PASS |
| Expected GM = P(sale\|negotiation)×E[GM\|sale] | PASS |
| smoothing / small sample | PASS |
| fallback | PASS |
| freshness (recency in stats; form UI-only) | PASS |
| capacity individual + team | PASS |
| baseline comparison | PASS |
| explainability | PASS |
| manual override + capacity guard | PASS |
| экономический эффект (baselines + sim) | PASS |
| MVP scope | PASS |
| технологии (FastAPI/React + ILP) | PASS |
| honesty: form/confidence/urgency not in optimal objective | PASS (в ZIP-доках) |

## Packaging

| Check | Result |
|-------|--------|
| ZIP exists | YES (~128 MB) |
| clean unzip → EXE start | PASS |
| health + frontend static | PASS |
| no `.venv` / `node_modules` / secrets / nested ZIPs | PASS |
| BAT launchers present | PASS |
| employer README in ZIP | PASS (запуск через BAT первым) |
| `build_release.bat` in ZIP | low clutter (не блокирует) |

## Documentation honesty

**В ZIP** (`docs/test_task_answer.md`, `architecture.md`): form / confidence / urgency описаны честно; assignment = ILP PuLP; proportional shrink не позиционируется как метод.

**Вне ZIP (корень репозитория):**

1. `README.md` всё ещё указывает старый ZIP `GermanWindows_AI_TestTask_Demo.zip` и `linear_sum_assignment` — **устарело**.  
   Серьёзность: **medium**, если работодателю отдают git/папку целиком; **low**, если только FINAL ZIP.  
   Минимальное исправление: обновить 2 абзаца в корневом README (после подтверждения).

2. В UI/API текстах причин (`reject_reason`, `explanation.reasons`) местами остаётся аббревиатура «GM».  
   Серьёзность: **low**.  
   Минимальное исправление: заменить на «ожидаемая валовая маржа» в 2–3 строках backend (после подтверждения).

3. Итог §18 в ответе: «учётом формы во времени» можно неверно прочитать как form-in-objective (хотя выше текст честный).  
   Серьёзность: **low**.

Код **не менялся** в этом аудите.

## Final verdict

```text
TECHNICAL_READY = YES
PRODUCT_READY = YES
DOCUMENTATION_READY = PARTIAL
PACKAGE_READY = YES
FINAL_READY = YES
```

`FINAL_READY = YES` означает: **пакет FINAL ZIP можно показывать работодателю**.  
`DOCUMENTATION_READY = PARTIAL` — из‑за устаревшего корневого `README.md` (не входит в ZIP) и остаточного «GM» в отдельных UI-строках.

Рекомендация перед отправкой (опционально, после подтверждения): обновить корневой README и 2–3 пользовательские строки с «GM». Пересобирать ZIP из‑за этого не обязательно, если работодатель получает только текущий FINAL ZIP + `README_ДЛЯ_РАБОТОДАТЕЛЯ.txt`.
