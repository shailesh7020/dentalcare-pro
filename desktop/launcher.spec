# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

BASE_DIR = Path(r"e:\dentalcare-pro\desktop").resolve()
ROOT_DIR = Path(r"e:\dentalcare-pro").resolve()

datas = [
    (str(ROOT_DIR / "assets" / "branding"), "assets/branding"),
    (str(BASE_DIR / "wizard.html"), "desktop"),
    (str(BASE_DIR / "splash.html"), "desktop"),
    (str(BASE_DIR / "wizard.html"), "."),
    (str(BASE_DIR / "splash.html"), "."),
]

hidden_imports = [
    "webview",
    "webview.platforms.winforms",
    "clr_loader",
    "pythonnet",
]

a = Analysis(
    [str(BASE_DIR / "launcher.py")],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "scipy", "torch"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DentalCarePro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hidden console for pure desktop experience
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(ROOT_DIR / "backend" / "version_info.txt"),
    icon=str(ROOT_DIR / "assets" / "branding" / "app_icon.ico"),
    manifest=str(ROOT_DIR / "backend" / "DentalCarePro.manifest"),
)
