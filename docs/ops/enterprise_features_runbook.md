# DentalCare Pro – Enterprise Commercial Features & Operations Runbook
**Phase 17 Enterprise Commercial Deployment Guide**
*Production Runbook & System Administrator Manual*

---

## 1. Overview
This runbook covers the operation, configuration, and maintenance of all enterprise deployment and commercial modules delivered in Phase 17 of DentalCare Pro:

1. **Professional Windows Installer & Distribution**: Single-click installation, desktop & start menu shortcuts, automatic PostgreSQL service detection, registry registration, uninstaller with data retention choice.
2. **Automatic Updates & Atomic Rollback**: Multi-channel version checking, pre-update database snapshots, SHA-256 cryptographic verification, atomic executable swap, automatic rollback on error.
3. **Encrypted Backups (AES-256) & Disaster Recovery**: Full PostgreSQL SQL dump + manifest + media bundling, Fernet AES-256 authenticated encryption, SHA-256 checksums, automated 30-day retention pruning, and single-click restore wizard.
4. **Clinician Digital Signatures**: Drawn and uploaded signatures, user-scoped storage, SHA-256 hash stamp, public verification endpoint (`/api/v1/signatures/verify/{hash}`).
5. **Clinical Document PDF Suite**: Vector PDF generation using ReportLab:
   - Prescriptions (with QR & signature)
   - Invoices & Receipts (with payment QR & authorized signature)
   - Treatment Plan Estimates (phased tooth-by-tooth procedures & patient acceptance line)
   - Medical Certificates (fitness/rest recommendations, diagnosis, clinic stamp)
   - Appointment Slips (kiosk check-in QR code, clinic instructions)
   - Informed Consent Forms (clinical risks, patient agreement, clinician counter-signature)
6. **Barcode & QR Code Engine**: ReportLab native vector Drawing flowables, Platypus Images, PNG Base64 data URLs, Code128 barcodes for patient files, kiosk check-in, invoice validation, and prescription authentication.
7. **Multi-User Clinic Network**: Real-time LAN synchronization over WebSockets (`/api/v1/network/ws/clinic/{clinic_id}`), workstation role tracking (`RECEPTION`, `DENTIST`, `ASSISTANT`, `MANAGER`, `ADMIN`), and clinic-wide broadcast events.
8. **Clinical File Storage with Anti-Virus Hook**: Categorized folders (`xrays/`, `photos/`, `documents/`, `consents/`, `invoices/`, `prescriptions/`), Windows Defender CLI (`MpCmdRun.exe`) integration with heuristic disguise detection, soft-delete and restore capability.
9. **Omnichannel Appointment Reminders & Follow-ups**: Automated 7-day, 3-day, 24-hour, and 2-hour multi-channel reminders, plus automated missed appointment follow-up workflows.
10. **Unified Admin Settings**: Single-pane configuration panel for clinic profile, working hours, chairs, backup schedules, reminder intervals, and gateway credentials.

---

## 2. Windows Installer & Release Pipeline
### Packaging the Release
To package a release bundle:
```powershell
python scripts/build_commercial_release.py
```
This script performs:
- Python and PostgreSQL toolchain verification (detects PostgreSQL 18, 17, 16).
- Database migrations to the latest revision.
- Distribution assembly in `dist/` and `Dental Clinic Management Gift/`.
- Release manifest creation in `dist/release_manifest.json`.

### Inno Setup Compilation
```powershell
ISCC.exe installer/DentalCarePro_Setup.iss
```
Output executable: `dist/installer/DentalCarePro-Setup-1.0.0.exe`.

---

## 3. Backup & Disaster Recovery Operations
### Creating an Encrypted Backup via API
```http
POST /api/v1/backups
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "backup_type": "MANUAL",
  "destination_type": "LOCAL",
  "is_encrypted": true,
  "password": "SecureClinicPassword2026!"
}
```

### Restoring from an Encrypted Backup
```http
POST /api/v1/backups/restore
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "backup_id": "c1f7b0e2-8d99-4a92-8e12-34567890abcd",
  "password": "SecureClinicPassword2026!"
}
```

### Command Line Backup Utility
```powershell
python desktop/backup_tool.py --backup
python desktop/backup_tool.py --restore "C:\DentalCarePro_Backups\dentalcare_backup_20260909_120000.dcb"
```

---

## 4. Clinician Digital Signatures
### Saving a Signature
Dentists and clinicians can capture a drawn or uploaded signature from the web or desktop UI:
```http
POST /api/v1/signatures
Authorization: Bearer <DENTIST_TOKEN>
Content-Type: application/json

{
  "signature_data": "data:image/png;base64,iVBORw0KGgo...",
  "signature_type": "DRAWN"
}
```

### Verifying a Document Signature
Anyone scanning the QR code or entering the document hash can verify authenticity:
```http
GET /api/v1/signatures/verify/{verification_hash}
```
Response:
```json
{
  "is_valid": true,
  "verification_hash": "a5f8...",
  "user_id": "...",
  "user_full_name": "Dr. Sarah Jenkins",
  "role": "DENTIST",
  "signed_at": "2026-09-09T14:15:00Z",
  "message": "Digital signature is cryptographically verified and authentic."
}
```

---

## 5. Multi-Workstation Real-Time Network Sync
Workstations in a clinic connect via WebSockets upon launch:
```
ws://127.0.0.1:8000/api/v1/network/ws/clinic/{clinic_id}?workstation_id=FRONT_DESK_01&workstation_role=RECEPTION
```

### Event Payload Format
```json
{
  "type": "BROADCAST",
  "event": "PATIENT_CHECKIN",
  "data": {
    "patient_id": "PAT-00123",
    "patient_name": "John Doe",
    "appointment_id": "APPT-5566",
    "chair_number": "1"
  }
}
```
All connected dentist and assistant workstations receive the update instantly with zero polling.

---

## 6. Anti-Virus & File Security
All clinical file uploads (`/api/v1/documents/upload`) pass through a two-stage security inspection:
1. **Heuristic Disguise Detection**: Validates file binary signatures to prevent malicious `.exe` / PE files masquerading as `.jpg`, `.png`, or `.pdf`.
2. **Windows Defender Deep Scan**: Invokes Microsoft Windows Defender CLI engine (`MpCmdRun.exe -Scan -ScanType 3 -File <path>`) for signature-level malware inspection.
3. Infected files are immediately unlinked from disk and rejected with HTTP 422.

---

## 7. Operational Troubleshooting
| Symptom | Cause | Solution |
|---|---|---|
| Backup tool reports "pg_dump not found" | Non-standard PostgreSQL location | Ensure PostgreSQL 18 is installed in `C:\Program Files\PostgreSQL\18\bin` or added to system PATH. |
| WebSockets disconnect periodically | LAN router timeout or firewall | WebSockets send keepalive `PING`/`PONG` frames every 30 seconds. Verify port 8000 is open on the host machine. |
| Antivirus scan times out | Windows Defender service busy | Heuristic scanner acts as fallback. Verify Windows Security service is running. |
| Inno Setup compiler missing | ISCC not in PATH | Install Inno Setup 6 from jrsoftware.org or run `ISCC.exe installer/DentalCarePro_Setup.iss` manually. |
