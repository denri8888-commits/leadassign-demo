"""FastAPI entrypoint — API + optional static SPA for portable demo."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ensure backend root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.routes import router

APP_VERSION = "1.0.0"

app = FastAPI(
    title="Lead Assignment Optimizer",
    description=(
        "Система не ищет лучшего менеджера вообще. Она ищет лучшее назначение "
        "конкретной заявки конкретному менеджеру с учётом ожидаемой GM и capacity."
    ),
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def _static_dir() -> Path | None:
    env = os.environ.get("LEADASSIGN_STATIC_DIR")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.extend(
        [
            ROOT / "static",
            ROOT.parent / "frontend" / "dist",
        ]
    )
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.insert(0, Path(sys._MEIPASS) / "static")  # type: ignore[attr-defined]
        candidates.insert(0, Path(sys.executable).resolve().parent / "static")
    for p in candidates:
        if (p / "index.html").exists():
            return p
    return None


STATIC_DIR = _static_dir()


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "details": [str(exc.__class__.__name__)],
            "hint": "Проверьте данные и настройки. Подробности traceback скрыты от пользователя.",
        },
    )


@app.get("/api")
def api_root():
    return {
        "name": "Lead Assignment Optimizer API",
        "docs": "/docs",
        "version": APP_VERSION,
        "core_idea": app.description,
        "demo_mode": True,
    }


if STATIC_DIR is not None:
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/")
    def spa_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # Do not shadow API / docs
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
else:

    @app.get("/")
    def root_api_only():
        return {
            "name": "Lead Assignment Optimizer API",
            "docs": "/docs",
            "version": APP_VERSION,
            "core_idea": app.description,
            "hint": "Frontend static не найден. Запустите через Vite или соберите portable.",
        }
