"""Portable entrypoint: API + static UI + browser open."""

from __future__ import annotations

import argparse
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _app_dir() -> Path:
    """Writable base for runtime/ (logs, pid, port)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        # release/app/GermanWindowsAI.exe → runtime в корне release/
        if exe_dir.name.lower() == "app":
            return exe_dir.parent
        return exe_dir
    return Path(__file__).resolve().parent


def _exe_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_root() -> Path:
    """Where bundled data lives (PyInstaller _MEIPASS or backend dir)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def find_free_port(preferred: int = 8000) -> int:
    for port in range(preferred, preferred + 40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # last resort
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def setup_runtime(base: Path) -> tuple[Path, Path, Path]:
    runtime = base / "runtime"
    logs = runtime / "logs"
    runtime.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    return runtime, logs, runtime / "app.pid"


def write_pid_port(runtime: Path, pid_file: Path, port: int) -> None:
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    (runtime / "port.txt").write_text(str(port), encoding="utf-8")


def wait_and_open(port: int, timeout: float = 60.0) -> None:
    import urllib.request

    url = f"http://127.0.0.1:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    webbrowser.open(f"http://127.0.0.1:{port}/")
                    return
        except Exception:
            time.sleep(0.4)
    # open anyway — user may still see startup page/errors
    webbrowser.open(f"http://127.0.0.1:{port}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="German Windows AI Demo")
    parser.add_argument("--port", type=int, default=0, help="Fixed port (0 = auto)")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    base = _app_dir()
    resources = _resource_root()
    runtime, logs, pid_file = setup_runtime(base)

    log_file = logs / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    log = logging.getLogger("portable")

    # Ensure import path for non-frozen runs
    backend_root = Path(__file__).resolve().parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    # Prefer bundled static next to exe, then inside _MEIPASS
    static_candidates = [
        _exe_dir() / "static",
        base / "static",
        resources / "static",
        backend_root / "static",
        backend_root.parent / "frontend" / "dist",
    ]
    static_dir = next((p for p in static_candidates if (p / "index.html").exists()), None)
    if static_dir:
        os.environ["LEADASSIGN_STATIC_DIR"] = str(static_dir)
        log.info("Static UI: %s", static_dir)
    else:
        log.warning("Static UI not found — API only mode")

    port = args.port if args.port > 0 else find_free_port(8000)
    write_pid_port(runtime, pid_file, port)
    log.info("Starting on http://%s:%s", args.host, port)
    log.info("PID %s written to %s", os.getpid(), pid_file)
    log.info("First start may take up to ~60s while the bundled runtime unpacks.")

    if not args.no_browser:
        threading.Thread(target=wait_and_open, args=(port, 120.0), daemon=True).start()

    import uvicorn

    from app.main import app

    @app.on_event("startup")
    async def _ready() -> None:
        log.info("Uvicorn startup complete — ready to serve")

    try:
        uvicorn.run(app, host=args.host, port=port, log_level="info")
    finally:
        try:
            if pid_file.exists() and pid_file.read_text(encoding="utf-8").strip() == str(os.getpid()):
                pid_file.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
