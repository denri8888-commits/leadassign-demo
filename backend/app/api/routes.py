from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from analytics.config import MANAGERS, PRODUCTS, REGIONS, SETTING_HELPERS, ModelSettings
from app.schemas.models import DemoGenerateRequest, OverrideRequest, SettingsUpdate, SimulationRequest
from app.services.state import STATE
from data.generator import SCENARIOS
from data.loader import apply_import, preview_import

router = APIRouter(prefix="/api")


def _need_result():
    if STATE.result is None:
        raise HTTPException(status_code=400, detail={"error": "Расчёт ещё не выполнен", "hint": "Сгенерируйте демо-день или пересчитайте."})
    return STATE.result


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": True,
        "core_idea": (
            "Система не ищет лучшего менеджера вообще. Она ищет лучшее назначение "
            "конкретной заявки конкретному менеджеру."
        ),
    }


@router.get("/dashboard")
def dashboard():
    return STATE.get_dashboard()


@router.get("/applications")
def applications(
    region: str | None = None,
    product: str | None = None,
    manager: str | None = None,
    selected: bool | None = None,
    confidence: str | None = None,
):
    result = _need_result()
    rows = result["recommendations"]
    if region:
        rows = [r for r in rows if r["region"] == region]
    if product:
        rows = [r for r in rows if r["product"] == product]
    if manager:
        rows = [r for r in rows if r.get("recommended_manager") == manager]
    if selected is not None:
        rows = [r for r in rows if r["selected"] is selected]
    if confidence:
        rows = [r for r in rows if r["confidence_label"] == confidence]
    return {"items": rows, "total": len(rows)}


@router.get("/applications/{application_id}")
def application_detail(application_id: str):
    result = _need_result()
    for r in result["recommendations"]:
        if r["application_id"] == application_id:
            return r
    raise HTTPException(status_code=404, detail={"error": "Заявка не найдена", "hint": "Проверьте ID."})


@router.get("/recommendations")
def recommendations():
    result = _need_result()
    return {
        "items": result["recommendations"],
        "kpi": result["kpi"],
        "baselines": {
            "random_gm": result["kpi"]["random_gm"],
            "manual_gm": result["kpi"]["manual_gm"],
            "greedy_gm": result["kpi"]["greedy_gm"],
            "optimal_gm": result["kpi"]["optimal_gm"],
        },
        "core_idea": result["core_idea"],
        "disclaimer": result["disclaimer"],
    }


@router.post("/recommendations/{application_id}/override")
def override(application_id: str, body: OverrideRequest):
    if body.manager not in MANAGERS:
        raise HTTPException(status_code=400, detail={"error": "Неизвестный менеджер", "hint": f"Допустимы: {', '.join(MANAGERS)}"})
    ids = set(STATE.applications["application_id"].astype(str))
    if application_id not in ids:
        raise HTTPException(status_code=404, detail={"error": "Заявка не найдена"})
    try:
        ov = STATE.override(application_id, body.manager, body.reason, body.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "hint": "Выберите менеджера со свободной загрузкой."})
    return {
        "ok": True,
        "override": ov,
        "application": next(r for r in STATE.result["recommendations"] if r["application_id"] == application_id),
    }


@router.get("/managers")
def managers():
    result = _need_result()
    hist = STATE.history
    items = []
    for m in MANAGERS:
        sub = hist[hist["manager"] == m]
        talks = len(sub)
        sales = int(sub["sale"].sum()) if talks else 0
        sold = sub[sub["sale"] == 1]
        items.append(
            {
                "manager": m,
                "form": result["forms"][m],
                "talks": talks,
                "sales": sales,
                "conversion": round(sales / talks, 4) if talks else 0,
                "avg_check": round(float(sold["sale_amount"].mean()), 2) if len(sold) else 0,
                "avg_gm": round(float(sold["gm"].mean()), 2) if len(sold) else 0,
                "avg_discount": round(float(sold["discount"].mean()), 3) if len(sold) and "discount" in sold.columns else 0,
                "load": result["manager_load"].get(m, 0),
                "capacity": STATE.settings.manager_capacities.get(m, 0),
            }
        )
    return {"items": items}


@router.get("/regions")
def regions():
    return {"items": REGIONS}


@router.get("/products")
def products():
    return {"items": PRODUCTS}


@router.get("/matrix")
def matrix():
    result = _need_result()
    return {"items": result["matrix"], "helpers": {"matrix": "Ожидаемая GM по сочетанию менеджер × регион × продукт на текущих заявках."}}


@router.get("/capacity")
def capacity():
    result = _need_result()
    return result["capacity_analysis"]


@router.get("/simulation")
def simulation(days: int = Query(14, ge=1, le=60), auto_share: float = Query(0.5, ge=0, le=1)):
    return STATE.simulation(days=days, auto_share=auto_share)


@router.get("/explanations/{application_id}")
def explanations(application_id: str):
    result = _need_result()
    for r in result["recommendations"]:
        if r["application_id"] == application_id:
            return r["explanation"]
    raise HTTPException(status_code=404, detail={"error": "Объяснение не найдено"})


@router.get("/settings")
def get_settings():
    return {"settings": STATE.settings.to_dict(), "helpers": SETTING_HELPERS, "scenarios": SCENARIOS}


@router.put("/settings")
def put_settings(body: SettingsUpdate):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "team_capacity" in data and data["team_capacity"] <= 0:
        raise HTTPException(status_code=400, detail={"error": "capacity должна быть > 0"})
    updated = STATE.update_settings(data)
    return {"settings": updated, "kpi": STATE.result["kpi"]}


@router.post("/recalculate")
def recalculate():
    result = STATE.recalculate()
    return {"ok": True, "kpi": result["kpi"], "timestamp": result["timestamp"]}


@router.post("/demo/generate")
def demo_generate(body: DemoGenerateRequest):
    if body.scenario not in SCENARIOS and body.scenario != "normal":
        raise HTTPException(status_code=400, detail={"error": "Неизвестный сценарий", "hint": f"Доступны: {', '.join(SCENARIOS)}"})
    STATE.generate_day(seed=body.seed, scenario=body.scenario)
    return {"ok": True, "dashboard": STATE.get_dashboard()}


@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), kind: str = Query("history")):
    content = await file.read()
    try:
        return preview_import(content, file.filename or "data.csv", kind=kind)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "Не удалось прочитать файл", "details": [str(e)], "hint": "Загрузите CSV или Excel."})


@router.post("/import/apply")
async def import_apply(
    file: UploadFile = File(...),
    kind: str = Query("history"),
    mapping_json: str = Query("{}"),
):
    import json

    content = await file.read()
    try:
        mapping = json.loads(mapping_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail={"error": "Некорректный mapping JSON"})
    df, errors = apply_import(content, file.filename or "data.csv", kind, mapping)
    if errors:
        raise HTTPException(status_code=400, detail={"error": "Ошибки валидации", "details": errors, "hint": "Исправьте файл или сопоставление колонок."})
    if kind == "history":
        # для анализа нужны и заявки — если только history, оставляем текущие applications
        STATE.history = df
        STATE.mode = "analysis"
        STATE.recalculate()
    else:
        STATE.applications = df
        STATE.mode = "analysis"
        STATE.recalculate()
    return {"ok": True, "rows": len(df), "kpi": STATE.result["kpi"], "mode": STATE.mode}


@router.get("/result")
def final_result():
    result = _need_result()
    k = result["kpi"]
    return {
        "title": "Результат сегодняшнего распределения",
        "total_applications": k["total_applications"],
        "assigned": k["recommended"],
        "queued": k["queued"],
        "expected_gm": k["expected_gm"],
        "lift_abs": k["lift_vs_manual_abs"],
        "lift_pct": k["lift_vs_manual_pct"],
        "disclaimer": "Показатели рассчитаны на демонстрационных данных.",
        "core_idea": result["core_idea"],
    }


@router.get("/assumptions")
def assumptions():
    return {
        "items": [
            {"title": "Лимит", "text": "Максимум 50 проведённых переговоров в день (настраивается)."},
            {"title": "Менеджеры", "text": "5 менеджеров по продажам."},
            {"title": "Capacity", "text": "Не требуется равное распределение по 10; лимиты гибкие, но индивидуальные."},
            {"title": "Данные", "text": "Синтетические демонстрационные данные, не реальные показатели компании."},
            {"title": "Новая заявка", "text": "Как минимум ID, дата, регион, продукт."},
        ]
    }


@router.get("/roadmap")
def roadmap():
    return {
        "next_features": [
            "источник заявки, история клиента, бюджет, длительность переговоров, причины отказа",
            "данные о конкурентах и сезонность — только после проверки влияния",
            "ML-модели как экспериментальный режим",
            "интеграция с CRM",
            "прогнозирование потребности в менеджерах",
        ],
        "note": "Сначала доказать пользу на доступных данных. Затем добавлять признаки только если они улучшают прогноз и допустимы.",
        "external_data": "Внешние социально-экономические данные возможны архитектурно, но не обязательны для MVP.",
        "demographics": "Пол/возраст не используются как прямой критерий ценности заявки.",
    }
