# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None

BASE_DIR = Path(r"e:\dentalcare-pro\backend").resolve()
ROOT_DIR = Path(r"e:\dentalcare-pro").resolve()

datas = [
    (str(BASE_DIR / "alembic.ini"), "."),
    (str(BASE_DIR / "migrations"), "migrations"),
    (str(ROOT_DIR / "assets" / "branding"), "assets/branding"),
]

hiddenimports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "sqlalchemy.ext.asyncio",
    "sqlalchemy.dialects.postgresql",
    "sqlalchemy.dialects.postgresql.asyncpg",
    "asyncpg",
    "alembic",
    "reportlab",
    "reportlab.lib",
    "reportlab.platypus",
    "bcrypt",
    "jwt",
    "app",
    "app.main",
    "app.api.v1.router",
    "app.core.config",
    "app.database.session",
    "app.models",
]

a = Analysis(
    [str(BASE_DIR / "desktop_entry.py")],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy"],
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
    name="DentalCarePro-API",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for API supervisor log streaming, hidden by launcher
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(BASE_DIR / "version_info.txt"),
    icon=str(ROOT_DIR / "assets" / "branding" / "app_icon.ico"),
    manifest=str(BASE_DIR / "DentalCarePro.manifest"),
)
