"""
Vercel Python entrypoint.

Весь трафик (API + собранный frontend) идёт через FastAPI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

# PYTHONPATH для analytics / optimization / app
for p in (str(BACKEND), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Статика после vercel build лежит в backend/static
os.environ.setdefault("LEADASSIGN_STATIC_DIR", str(BACKEND / "static"))

from app.main import app  # noqa: E402

# ASGI export for Vercel Python runtime
__all__ = ["app"]
