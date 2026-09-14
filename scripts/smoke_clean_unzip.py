"""Clean-unzip smoke for FINAL package."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

TMP = Path(r"d:/LeadAssign_FINAL_clean_test")
EXE = TMP / "app" / "GermanWindowsAI.exe"


def http_json(method: str, url: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main() -> None:
    # kill previous if any
    pid_file = TMP / "runtime" / "app.pid"
    port_file = TMP / "runtime" / "port.txt"
    if pid_file.exists():
        try:
            import os

            os.kill(int(pid_file.read_text().strip()), 9)
        except Exception:
            pass
        time.sleep(1)
    for f in (pid_file, port_file):
        if f.exists():
            f.unlink()

    proc = subprocess.Popen(
        [str(EXE)],
        cwd=str(TMP / "app"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    port = None
    for _ in range(90):
        time.sleep(1)
        if port_file.exists():
            candidate = port_file.read_text().strip()
            try:
                st, health = http_json("GET", f"http://127.0.0.1:{candidate}/api/health")
                if st == 200 and health.get("status") == "ok":
                    port = candidate
                    break
            except Exception:
                pass
        if proc.poll() is not None:
            raise SystemExit(f"exe exited early code={proc.returncode}")
    if not port:
        raise SystemExit("no port")

    base = f"http://127.0.0.1:{port}"
    st, health = http_json("GET", f"{base}/api/health")
    assert st == 200 and health["status"] == "ok"
    st, dash = http_json("GET", f"{base}/api/dashboard")
    kpi = dash["kpi"]
    assert kpi["total_applications"] == 70
    assert kpi["recommended"] == 50
    assert kpi["queued"] == 20

    st, apps = http_json("GET", f"{base}/api/applications?selected=true")
    item = apps["items"][0]
    aid = item["application_id"]
    st, detail = http_json("GET", f"{base}/api/applications/{aid}")
    assert "expected_gm" in detail
    assert detail.get("recommended_manager") or detail.get("best_available_manager")

    # capacity reject
    load = dash["manager_load"]
    full = next(m for m, c in load.items() if c >= 10)
    st, body = http_json(
        "POST",
        f"{base}/api/recommendations/{aid}/override",
        {"manager": full, "reason": "test full", "comment": ""},
    )
    assert st == 400, body

    # create free slots
    st, settings = http_json("PUT", f"{base}/api/settings", {"team_capacity": 45})
    assert st == 200, settings
    st, dash = http_json("GET", f"{base}/api/dashboard")
    load = dash["manager_load"]
    st, apps = http_json("GET", f"{base}/api/applications?selected=true")
    item = apps["items"][0]
    aid = item["application_id"]
    orig = item["recommended_manager"]
    free = next(m for m, c in load.items() if c < 10 and m != orig)
    st, body = http_json(
        "POST",
        f"{base}/api/recommendations/{aid}/override",
        {"manager": free, "reason": "уже работает", "comment": "clean unzip"},
    )
    assert st == 200, body
    ov = body["application"]["override"]
    assert ov["original_manager"] == orig
    assert ov["manual_manager"] == free

    print(
        json.dumps(
            {
                "CLEAN_UNZIP_SMOKE": "PASS",
                "port": port,
                "kpi": {
                    "total": 70,
                    "selected": 50,
                    "queued": 20,
                    "after_settings_selected": dash["kpi"]["recommended"],
                },
                "override": {
                    "original": ov["original_manager"],
                    "manual": ov["manual_manager"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


if __name__ == "__main__":
    main()
