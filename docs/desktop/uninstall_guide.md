# DentalCare Pro – Workstation Uninstallation & Data Retention Guide

This guide explains how to uninstall **DentalCare Pro Enterprise** while complying with healthcare record retention laws.

---

## 1. HIPAA Patient Data Retention Mandate

> [!IMPORTANT]
> Medical and dental regulations (including HIPAA, ADA, and state dental boards) mandate that patient electronic health records must be retained for **at least 6 to 10 years** depending on the jurisdiction.

DentalCare Pro includes an automated uninstallation safeguard to prevent accidental loss of clinical history.

---

## 2. Standard Uninstallation Process

### Step 1: Launch Uninstaller
You can initiate uninstallation via either:
1. **Windows Settings**: Open **Settings** → **Apps** → **Installed Apps** → Find **DentalCare Pro Enterprise** → Click **Uninstall**.
2. **Direct Executable**: Run `C:\Program Files\DentalCare Pro\uninstall.exe`.

### Step 2: HIPAA Data Safeguard Prompt
The uninstaller window appears with the prompt:
- **"Retain patient database and backups (Recommended)"** [Checked by default]

- **If Checked**:
  - Application executables, shortcuts, and registry keys are removed.
  - Your patient database, odontograms, DICOM radiographs, logs, and `C:\DentalCarePro_Backups` **remain completely safe and untouched**.
  - Reinstalling DentalCare Pro in the future will immediately reconnect to your existing data.

- **If Unchecked**:
  - All local application files, including `%LOCALAPPDATA%\DentalCarePro`, are removed from this workstation.
  - This option should only be used when decommissioning a workstation permanently after offsite backups have been confirmed.

---

## 3. Silent IT Uninstallation

For enterprise administrators deploying via Microsoft Endpoint Configuration Manager (SCCM) or Intune:
```cmd
"C:\Program Files\DentalCare Pro\uninstall.exe" /VERYSILENT /SUPPRESSMSGBOXES
```
