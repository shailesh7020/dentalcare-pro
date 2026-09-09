# DentalCare Pro – Enterprise Update & Maintenance Guide

This guide outlines the update and version management architecture for **DentalCare Pro Enterprise**.

---

## 1. Overview & Data Safety Guarantee

DentalCare Pro updates are designed for zero data loss:
- Application binaries (`DentalCarePro.exe`, `backend/DentalCarePro-API.exe`) are upgraded atomically.
- Clinic databases, electronic health records (EHR), odontograms, radiographs, and configurations stored in `%LOCALAPPDATA%\DentalCarePro` and PostgreSQL are **never deleted or overwritten** during an update.
- An automatic pre-update snapshot is captured in `%LOCALAPPDATA%\DentalCarePro\snapshots\` before any binary files are modified.

---

## 2. Automatic & Manual Update Procedures

### A. Updating via Standalone Distribution Package
1. Obtain the new version distribution folder (e.g., `Dental Clinic Management Gift`).
2. Run `Install DentalCare Pro.exe`.
3. The setup wizard automatically detects the existing installation at `C:\Program Files\DentalCare Pro`.
4. Click **Install**. Setup safely updates the runtime binaries and triggers programmatic Alembic migrations on startup.

### B. Command-Line Atomic Update with Rollback
The updater tool (`updater.exe`) provides atomic rollback:
```cmd
updater.exe --check
updater.exe --apply "D:\Updates\v1.0.1" --target-dir "C:\Program Files\DentalCare Pro"
```
If any file replacement fails or the health check returns non-200, `updater.exe` automatically rolls back to the previous snapshot.

---

## 3. Database Migration Lifecycle

When a new version is launched:
1. The backend (`DentalCarePro-API.exe`) executes `alembic.command.upgrade(cfg, 'head')` programmatically.
2. PostgreSQL transactions ensure schema additions or index changes are atomic.
3. If an Alembic migration encounters an error, the backend logs the fault in `%LOCALAPPDATA%\DentalCarePro\logs\backend.log` and refuses to start with an incompatible schema.

---

## 4. Rollback Plan

If a clinic needs to revert to an earlier version:
1. Stop the `DentalCarePro.exe` application.
2. Restore the previous binary directory from `%LOCALAPPDATA%\DentalCarePro\snapshots\snapshot_YYYYMMDD_HHMMSS`.
3. If database changes were applied, restore the pre-update backup using:
   ```cmd
   backup_manager.exe --restore "C:\DentalCarePro_Backups\dentalcare_backup_YYYYMMDD_HHMMSS.sql"
   ```
4. Restart DentalCare Pro.
