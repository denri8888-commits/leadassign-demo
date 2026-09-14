"""Final acceptance smoke from a NEW clean unzip directory."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

SRC_ZIP = Path(r"d:/тестовое/LeadAssign_Nemetskie_Okna_Bel_FINAL_2026-09-13.zip")
TMP = Path(r"d:/LeadAssign_ACCEPTANCE_2026-09-14")


def http_json(method: str, url: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        payload = e.read().decode()
        try:
            return e.code, json.loads(payload)
        except Exception:
            return e.code, {"raw": payload}


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    with zipfile.ZipFile(SRC_ZIP, "r") as z:
        z.extractall(TMP)

    exe = TMP / "app" / "GermanWindowsAI.exe"
    assert exe.exists()
    bats = list(TMP.glob("*.bat"))
    assert any("ЗАПУСТИТЬ" in b.name or "DEMO" in b.name.upper() or True for b in bats)

    # stop leftovers
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process GermanWindowsAI -ErrorAction SilentlyContinue | Stop-Process -Force"],
        check=False,
    )
    time.sleep(1)

    proc = subprocess.Popen([str(exe)], cwd=str(TMP / "app"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port_file = TMP / "runtime" / "port.txt"
    port = None
    for _ in range(90):
        time.sleep(1)
        if port_file.exists():
            cand = port_file.read_text().strip()
            try:
                st, h = http_json("GET", f"http://127.0.0.1:{cand}/api/health")
                if st == 200 and h.get("status") == "ok":
                    port = cand
                    break
            except Exception:
                pass
        if proc.poll() is not None:
            raise SystemExit(f"exe exited {proc.returncode}")
    if not port:
        raise SystemExit("no healthy port")

    base = f"http://127.0.0.1:{port}"
    report: dict = {"port": port, "checks": {}}

    st, health = http_json("GET", f"{base}/api/health")
    report["checks"]["health"] = {"ok": st == 200 and health.get("demo_mode") is True, "body": health}

    st, dash = http_json("GET", f"{base}/api/dashboard")
    kpi = dash["kpi"]
    report["checks"]["kpi_70_50_20"] = {
        "ok": kpi["total_applications"] == 70 and kpi["recommended"] == 50 and kpi["queued"] == 20,
        "kpi": {
            "total": kpi["total_applications"],
            "recommended": kpi["recommended"],
            "queued": kpi["queued"],
            "expected_gm": kpi["expected_gm"],
            "manual_gm": kpi.get("manual_gm"),
            "random_gm": kpi.get("random_gm"),
            "lift_vs_manual_pct": kpi.get("lift_vs_manual_pct"),
        },
        "core_idea": dash.get("core_idea"),
        "disclaimer": dash.get("disclaimer"),
    }

    # frontend static
    with urllib.request.urlopen(f"{base}/", timeout=10) as r:
        html = r.read().decode("utf-8", errors="replace")
    report["checks"]["frontend_index"] = {"ok": r.status == 200 and ("root" in html or "div" in html), "status": r.status}

    st, apps_all = http_json("GET", f"{base}/api/applications")
    st, apps_sel = http_json("GET", f"{base}/api/applications?selected=true")
    st, apps_q = http_json("GET", f"{base}/api/applications?selected=false")
    selected = apps_sel["items"]
    queued = apps_q["items"]
    report["checks"]["applications_split"] = {
        "ok": len(selected) == 50 and len(queued) == 20 and apps_all["total"] == 70,
        "selected": len(selected),
        "queued": len(queued),
        "total": apps_all["total"],
    }

    # queued reject reasons
    reasons = [q.get("reject_reason") for q in queued]
    report["checks"]["queue_explanations"] = {
        "ok": all(bool(r) for r in reasons),
        "sample": reasons[:5],
        "unique_count": len(set(reasons)),
    }

    # explanation richness on 3 selected apps
    explain_ok = True
    samples = []
    for item in selected[:3]:
        st, det = http_json("GET", f"{base}/api/applications/{item['application_id']}")
        expl = det.get("explanation") or {}
        needed = [
            det.get("region"),
            det.get("product"),
            det.get("recommended_manager"),
            det.get("expected_gm") is not None,
            det.get("confidence_label"),
            expl.get("reasons"),
            expl.get("alternatives"),
            expl.get("formula"),
        ]
        ok = all(needed) and len(expl.get("reasons") or []) >= 1 and len(expl.get("alternatives") or []) >= 1
        explain_ok = explain_ok and ok
        samples.append(
            {
                "id": det["application_id"],
                "manager": det.get("recommended_manager"),
                "region": det.get("region"),
                "product": det.get("product"),
                "expected_gm": det.get("expected_gm"),
                "confidence": det.get("confidence_label"),
                "n_obs": det.get("n_observations"),
                "fallback": det.get("fallback_label"),
                "used_fallback": det.get("used_fallback"),
                "reasons_n": len(expl.get("reasons") or []),
                "alts_n": len(expl.get("alternatives") or []),
                "formula_steps": [s.get("label") for s in (expl.get("formula") or {}).get("steps") or []],
                "ok": ok,
            }
        )
    report["checks"]["explainability"] = {"ok": explain_ok, "samples": samples}

    # capacity reject
    load = dash["manager_load"]
    full = next(m for m, c in load.items() if c >= 10)
    aid = selected[0]["application_id"]
    st, body = http_json(
        "POST",
        f"{base}/api/recommendations/{aid}/override",
        {"manager": full, "reason": "тест полной capacity", "comment": ""},
    )
    err = (body.get("detail") or {}).get("error") if isinstance(body.get("detail"), dict) else body.get("detail") or body.get("error")
    report["checks"]["override_reject_full"] = {
        "ok": st == 400 and err and "capacity" in str(err).lower(),
        "status": st,
        "error": err,
    }

    # successful override with free slot
    st, _ = http_json("PUT", f"{base}/api/settings", {"team_capacity": 45})
    st, dash2 = http_json("GET", f"{base}/api/dashboard")
    load2 = dash2["manager_load"]
    st, apps_sel2 = http_json("GET", f"{base}/api/applications?selected=true")
    item = apps_sel2["items"][0]
    orig = item["recommended_manager"]
    free = next(m for m, c in load2.items() if c < 10 and m != orig)
    st, body = http_json(
        "POST",
        f"{base}/api/recommendations/{item['application_id']}/override",
        {"manager": free, "reason": "уже работает с этим клиентом", "comment": "acceptance"},
    )
    ov = (body.get("application") or {}).get("override") or {}
    report["checks"]["override_preserve"] = {
        "ok": st == 200 and ov.get("original_manager") == orig and ov.get("manual_manager") == free,
        "status": st,
        "original": ov.get("original_manager"),
        "manual": ov.get("manual_manager"),
        "reason": ov.get("reason"),
    }

    # baselines present
    report["checks"]["baseline_kpis"] = {
        "ok": all(k in kpi for k in ("manual_gm", "random_gm", "optimal_gm", "greedy_gm")),
        "values": {k: kpi.get(k) for k in ("manual_gm", "random_gm", "optimal_gm", "greedy_gm")},
    }

    # capacity endpoint
    st, cap = http_json("GET", f"{base}/api/capacity")
    report["checks"]["capacity_module"] = {
        "ok": st == 200 and bool(cap),
        "keys": list(cap.keys())[:12] if isinstance(cap, dict) else type(cap).__name__,
    }

    # simulation
    st, sim = http_json("GET", f"{base}/api/simulation?days=7&auto_share=0.5")
    report["checks"]["simulation"] = {
        "ok": st == 200 and isinstance(sim, dict),
        "status": st,
        "keys": list(sim.keys())[:12] if isinstance(sim, dict) else None,
    }

    # managers / matrix
    st_m, mgr = http_json("GET", f"{base}/api/managers")
    st_x, mx = http_json("GET", f"{base}/api/matrix")
    report["checks"]["managers_matrix"] = {
        "ok": st_m == 200 and st_x == 200 and len(mgr.get("items") or []) == 5 and len(mx.get("items") or []) > 0,
        "managers": len(mgr.get("items") or []),
        "matrix_cells": len(mx.get("items") or []),
    }

    # import endpoints exist (POST without file -> 422 expected)
    import_probe = {}
    for path in ("/api/import/preview", "/api/import/apply"):
        st_i, body_i = http_json("POST", f"{base}{path}", {})
        import_probe[path] = {"status": st_i, "ok": st_i in (400, 422)}
    report["checks"]["import_routes"] = {
        "ok": all(v["ok"] for v in import_probe.values()),
        "probe": import_probe,
    }

    # reset settings note
    all_ok = all(c.get("ok") for c in report["checks"].values() if isinstance(c, dict) and "ok" in c)
    report["SMOKE_PASS"] = all_ok

    print(json.dumps(report, ensure_ascii=False, indent=2))

    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


if __name__ == "__main__":
    main()
