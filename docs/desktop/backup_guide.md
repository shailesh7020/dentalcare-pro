# DentalCare Pro – Clinic Backup & Disaster Recovery Guide

This guide details database backup, scheduling, export/import, and disaster recovery procedures for **DentalCare Pro Enterprise**.

---

## 1. Backup Architecture

Under HIPAA § 164.308(a)(7)(ii)(A), dental practices are required to establish and maintain retrievable exact copies of electronic protected health information (ePHI).

DentalCare Pro implements a multi-tier backup engine:
1. **Automated Daily Backups**: Checks backup age every 24 hours and takes a snapshot to `C:\DentalCarePro_Backups\`.
2. **On-Demand Manual Backups**: Created prior to major software updates or server maintenance.
3. **Emergency SQL Dump Export**: Portably exports full clinical schemas and records for offsite archiving.

---

## 2. Using the Backup Utility (`backup_manager.exe`)

The standalone backup binary is located in `C:\Program Files\DentalCare Pro\backup_manager.exe`:

### Create an Immediate Manual Backup:
```cmd
backup_manager.exe --backup
```
Output:
```
[2026-09-09 12:35:00] Starting database backup to C:\DentalCarePro_Backups\dentalcare_backup_20260909_123500.sql...
[2026-09-09 12:35:03] Backup created successfully (1248020 bytes).
```

### Check Daily Automated Schedule:
```cmd
backup_manager.exe --daily-schedule
```

### Restore a Database from Backup:
```cmd
backup_manager.exe --restore "C:\DentalCarePro_Backups\dentalcare_backup_20260909_123500.sql"
```

### Export SQL for External Media (USB / Offsite NAS):
```cmd
backup_manager.exe --export-sql "E:\Encrypted_Clinic_Backup\dentalcare_export.sql"
```

---

## 3. Best Practices for Dental Practices

1. **3-2-1 Rule**:
   - Keep 3 copies of your data (Live database, Local backup on `C:\DentalCarePro_Backups`, and 1 Offsite copy).
   - Use 2 different media types (Local SSD and Encrypted External Hard Drive).
   - Store 1 copy off-site or on an encrypted clinical cloud drive.
2. **Encryption**: All backup files containing ePHI should be stored on BitLocker-encrypted drives.
3. **Periodic Test Restores**: Test restoring a backup once every quarter to a secondary staging workstation.
