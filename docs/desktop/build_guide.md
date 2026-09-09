# DentalCare Pro – Desktop Build & Packaging Guide

This guide provides technical instructions for software engineers and release managers to compile, package, and sign DentalCare Pro for Windows.

---

## 1. Prerequisites

- Windows 10 or 11 (64-bit)
- Python 3.12 or 3.13 with PyInstaller (`pip install pyinstaller pillow`)
- Node.js 20+ and pnpm
- Inno Setup 6 (download from https://jrsoftware.org/isdl.php)
- Windows SDK with `signtool.exe` (for production code signing)

---

## 2. Automated One-Click Build Pipeline

Run the master packaging orchestrator from the repository root:
```bash
python scripts/desktop/build_installer.py
```
This script automatically:
1. Generates multi-resolution Windows ICO and splash screen assets.
2. Compiles `backend/desktop_entry.py` into `dist/backend/DentalCarePro-API.exe` with PyInstaller.
3. Compiles `desktop/launcher.py` into `dist/DentalCarePro.exe`.
4. Assembles the standalone portable distribution folder and creates `dist/DentalCarePro-v1.0.0-Portable.zip`.
5. Invokes `iscc.exe` to compile the single-file commercial installer `dist/installer/DentalCarePro-Setup-1.0.0.exe`.
6. Computes SHA256 checksums in `dist/checksums.sha256`.

---

## 3. Manual Step-by-Step Build Commands

### Step 3.1: Generate Branding Assets
```bash
python scripts/desktop/generate_assets.py
```

### Step 3.2: Build Backend Standalone Binary
```bash
python scripts/desktop/build_backend.py
```
This invokes PyInstaller using `backend/dentalcare_api.spec`, bundling FastAPI, Uvicorn, SQLAlchemy, Alembic migration scripts, and reportlab into `dist/backend/DentalCarePro-API.exe`.

### Step 3.3: Build Windows Desktop Launcher
```bash
pyinstaller --distpath=dist --workpath=build/desktop desktop/launcher.spec
```

### Step 3.4: Build Next.js Production Standalone Frontend
```bash
cd apps/web
pnpm build
```

### Step 3.5: Compile Inno Setup Installer
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer/DentalCarePro_Setup.iss
```

---

## 4. Production Code Signing

Sign all binaries and the installer package using your EV Code Signing certificate:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/desktop/sign_binaries.ps1 -CertificatePath "C:\certs\dentalcare_ev.pfx" -CertificatePassword "YourPass"
```
This applies SHA256 digital signatures with RFC 3161 timestamps, preventing Windows Defender SmartScreen warnings.
