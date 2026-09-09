# DentalCare Pro – Desktop Troubleshooting & Diagnostics Guide

This guide resolves common installation, networking, and runtime issues encountered on Windows workstations.

---

## 1. Diagnostic Log Locations

All application runtime logs are stored in standard Windows AppData:
- **Path**: `%LOCALAPPDATA%\DentalCarePro\logs` (e.g., `C:\Users\<Username>\AppData\Local\DentalCarePro\logs`)
- **Key Log Files**:
  - `backend.log`: FastAPI core server operations, SQL queries, and error traces.
  - `supervisor.log`: Process launcher and health monitor status.
  - `launcher.log`: Desktop application window launch logs.

---

## 2. Common Issues & Solutions

### Issue 1: "Database connection failed" during Setup Wizard
- **Cause**: PostgreSQL service is stopped or port 5432 is blocked.
- **Solution**:
  1. Open Windows Services (`services.msc`).
  2. Find `postgresql-x64-16` and ensure status is **Running**.
  3. If connecting to a central clinic server, verify you can ping the server IP and that port 5432 is allowed in Windows Firewall:
     ```powershell
     Test-NetConnection -ComputerName 192.168.1.100 -Port 5432
     ```

### Issue 2: "Port 8000 already in use"
- **Cause**: Another service or prior instance is holding port 8000.
- **Solution**:
  1. Open `%LOCALAPPDATA%\DentalCarePro\config.json`.
  2. Change `"PORT": 8000` to `"PORT": 8088` (or any available port).
  3. Restart DentalCare Pro.

### Issue 3: Windows Defender SmartScreen "Unknown Publisher" Warning
- **Cause**: The application installer is newly compiled and has not yet built SmartScreen reputation with an EV Code Signing certificate.
- **Solution**:
  1. Click **More info**.
  2. Click **Run anyway**.
  3. For enterprise clinic rollouts, sign the binaries using `scripts/desktop/sign_binaries.ps1` with your organization's trusted code signing certificate.

### Issue 4: Resetting Configuration to Factory Defaults
If configuration was entered incorrectly:
1. Close DentalCare Pro.
2. Delete `%LOCALAPPDATA%\DentalCarePro\config.json`.
3. Re-launch DentalCare Pro. The First-Launch Setup Wizard will re-appear.
