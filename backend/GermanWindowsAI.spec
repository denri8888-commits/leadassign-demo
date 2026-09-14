# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [("static", "static")]
datas += collect_data_files("uvicorn")
try:
    datas += collect_data_files("scipy")
except Exception:
    pass
try:
    datas += collect_data_files("pulp")
except Exception:
    pass

hiddenimports = (
    collect_submodules("analytics")
    + collect_submodules("optimization")
    + collect_submodules("data")
    + collect_submodules("app")
    + collect_submodules("pulp")
    + [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "multipart",
        "openpyxl",
        "pulp",
    ]
)

a = Analysis(
    ["run_portable.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "IPython", "notebook", "sklearn"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="GermanWindowsAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
