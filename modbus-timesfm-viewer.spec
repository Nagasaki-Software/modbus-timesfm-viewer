# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = []
datas += collect_data_files("timesfm")
datas += collect_data_files("pymodbus")
hiddenimports = collect_submodules("timesfm") + collect_submodules("pymodbus")

a = Analysis(
    ["app/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="modbus-timesfm-viewer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
