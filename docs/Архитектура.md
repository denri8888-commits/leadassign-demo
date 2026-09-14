# Архитектура MVP: распределение заявок и ожидаемая GM

## 1. Цель системы

Система не ищет «лучшего менеджера вообще».  
Она ищет лучшее назначение **конкретной заявки конкретному менеджеру** с учётом ожидаемого экономического результата и ограниченной мощности команды (70 заявок → до 50 переговоров).

Бизнес-цель: увеличить **ожидаемую валовую маржу (GM)** при capacity ≈ 50 переговоров в день.

---

## 2. Структура репозитория

```
/
├── README.md
├── docs/                    # бизнес- и техдокументация
├── data/                    # демо CSV / SQLite
├── backend/
│   ├── app/                 # FastAPI: API, схемы, сервисы состояния
│   ├── analytics/           # метрики, конверсия, GM, форма, confidence, explain
│   ├── optimization/        # greedy, optimal assignment, baseline, capacity
│   └── data/                # генератор синтетики, loader, validation
├── frontend/                # React + Vite + TypeScript
└── tests/                   # unit / integration / scenario
```

---

## 3. Поток данных

```
История сделок (demo/CSV)
        ↓
  metrics + recency + smoothing
        ↓
  оценка пар заявка × менеджер (Expected GM, confidence)
        ↓
  оптимизатор (greedy | optimal) + baselines
        ↓
  рекомендации + объяснения + KPI
        ↓
  FastAPI → React dashboard
```

Новая заявка содержит только известное **до** переговоров: id, дата, регион, продукт (+ опционально источник, тип клиента, срочность).  
Поля продажи / GM / скидки используются **только** для исторической статистики — без data leakage.

---

## 4. Модули backend

| Модуль | Назначение |
|--------|------------|
| `data/generator.py` | Синтетика с seed и сценариями |
| `data/loader.py` | Загрузка CSV/Excel, маппинг колонок |
| `data/validation.py` | Проверки целостности |
| `analytics/recency.py` | Экспоненциальное затухание |
| `analytics/conversion.py` | Сглаженная конверсия (Bayesian prior) |
| `analytics/gm_model.py` | Expected GM |
| `analytics/confidence.py` | Уверенность + fallback hierarchy |
| `analytics/form.py` | Текущая форма менеджера |
| `analytics/scoring.py` | Оценка пары заявка × менеджер |
| `analytics/explanation.py` | Текстовые причины рекомендации |
| `optimization/greedy.py` | Жадное назначение |
| `optimization/optimal.py` | ILP PuLP/CBC: full caps + team_capacity |
| `optimization/baseline.py` | Random + «лучший по истории R×P» |
| `optimization/capacity.py` | Сценарии 40…70 и экономика найма |
| `optimization/simulation.py` | Симулятор эффекта |
| `app/main.py` | FastAPI entry |
| `app/api/*` | REST endpoints |
| `app/services/state.py` | In-memory demo state + кэш расчёта |

---

## 5. Модель оценки (прозрачная статистика)

### 5.1. Сглаженная конверсия

```
adjusted_p = (weighted_successes + prior_strength * global_p)
           / (weighted_trials + prior_strength)
```

### 5.2. Временные веса

```
weight = exp(-λ * days_old)
```

### 5.3. Expected GM

```
Expected GM = adjusted_p × expected_GM_per_successful_deal
```

где `expected_GM_per_successful_deal` — взвешенное среднее GM успешных сделок на выбранном уровне fallback.

### 5.4. Fallback hierarchy (каждый шаг снижает confidence)

1. менеджер + регион + продукт  
2. менеджер + регион  
3. менеджер + продукт  
4. менеджер  
5. регион + продукт  
6. глобальная статистика  

---

## 6. Распределение (задача B)

Ограничения:

- суммарно ≤ team capacity (по умолчанию 50);
- ≤ individual capacity менеджера;
- одна заявка — один менеджер;
- одновременно выбираются **какие** заявки и **кому**.

**Optimal:** ILP (PuLP CBC): `maximize Σ ExpectedGM(i,m)·x(i,m)` при ограничениях «одна заявка — не более одного менеджера», полные индивидуальные `capacity_m` и `team_capacity`. Пропорциональное сжатие слотов не используется.  
История для scoring: только `date < as_of` (`historical_data`).  
Manual override сохраняет исходную рекомендацию и не нарушает capacity.  
**Greedy:** сортировка пар по Expected GM с учётом capacity.  
**Baselines:** random; «лучшая историческая GM по регион+продукт».

---

## 7. API (основные)

- `GET /api/dashboard`
- `GET /api/applications`, `GET /api/applications/{id}`
- `GET /api/managers`, `GET /api/regions`, `GET /api/products`
- `GET /api/recommendations`
- `POST /api/recommendations/{id}/override`
- `GET /api/capacity`, `GET /api/simulation`
- `GET /api/explanations/{application_id}`
- `GET|PUT /api/settings`
- `POST /api/demo/generate`
- `POST /api/import/preview`, `POST /api/import/apply`
- `POST /api/recalculate`

Ответы — Pydantic-схемы; ошибки — понятные JSON без traceback.

---

## 8. Frontend

React + Vite + TypeScript + Tailwind + Recharts.

Экраны:

1. Распределение заявок (KPI + графики)  
2. Рекомендации (таблица + drawer)  
3. Менеджеры  
4. Регионы и товары (heatmap)  
5. Аналитика capacity  
6. Проверка эффекта  
7. Настройки модели  
8. Импорт данных  
9. Результат дня (финальный экран демо)  
10. Допущения / будущее развитие  

Тема: светлый B2B, белый/серый фон, красный акцент (ориентир «Немецкие ОКНА»), токены CSS variables.

---

## 9. Настройки (видимые в UI)

- capacity команды и менеджеров  
- λ (вес свежести)  
- prior_strength (сглаживание)  
- min_observations  
- стоимость доп. менеджера / мес  
- рабочих дней в месяце  

---

## 10. Сознательные упрощения MVP

- без CRM, auth, LLM-чата;  
- без нейросети в основном режиме;  
- без внешних социально-экономических данных;  
- без моделирования конкурентов;  
- SQLite/in-memory для демо, не production-хранилище.

---

## 11. Порядок реализации

1. Генератор данных  
2. Analytics core  
3. Optimizer + baseline + capacity  
4. Backend API  
5. Frontend  
6. Tests + docs  

Приоритет: **корректность бизнес-логики → понятность → стабильность → скорость → UI → доп. функции**.
