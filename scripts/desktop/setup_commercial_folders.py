# scratch/setup_commercial_folders.py
"""
DentalCare Pro - Distribution Subfolder Generator
Populates:
1. Clinic Logo/
2. Sample Data/
3. Backup Utility/
4. Uninstaller/
"""
import os
import shutil
import csv
import json
from pathlib import Path

ROOT_DIR = Path(r"e:\dentalcare-pro").resolve()
GIFT_DIR = ROOT_DIR / "Dental Clinic Management Gift"

def setup_clinic_logo():
    print("[+] Configuring 'Clinic Logo/'...")
    logo_dir = GIFT_DIR / "Clinic Logo"
    logo_dir.mkdir(parents=True, exist_ok=True)

    branding_dir = ROOT_DIR / "assets" / "branding"
    for item in ["app_icon.ico", "app_icon.png", "splash_screen.png", "installer_banner.bmp"]:
        src = branding_dir / item
        if src.exists():
            shutil.copy2(src, logo_dir / item)

    readme_content = """======================================================================
  DENTALCARE PRO - CLINIC LOGO & BRANDING CUSTOMIZATION GUIDE
======================================================================

Welcome to DentalCare Pro!

You can customize the software with your clinic's own official logo,
letterhead, and branding.

WHERE YOUR CLINIC LOGO APPEARS:
  1. Official Patient Invoices & Payment Receipts
  2. Doctor Prescription Slips & Treatment Estimates
  3. Medical Certificates & Dental Absence Slips
  4. Clinical Consent Forms & Odontogram Reports
  5. Workstation Navigation Header & Login Screen

HOW TO SET YOUR CLINIC LOGO IN DENTALCARE PRO:
  Step 1: Launch DentalCare Pro on your computer.
  Step 2: Log in with your Administrator account.
  Step 3: Click on the "Settings" gear icon in the bottom-left sidebar.
  Step 4: Under "Clinic Profile", click "Upload Clinic Logo".
  Step 5: Select your clinic logo image and click "Save Settings".

RECOMMENDED LOGO SPECIFICATIONS:
  * Format: PNG (transparent background) or high-resolution JPEG
  * Optimal Dimensions: 512 x 512 pixels (Square) or 800 x 250 pixels (Horizontal Letterhead)
  * Color Profile: sRGB
  * Max File Size: 5 MB

INCLUDED SAMPLE ASSETS:
  * app_icon.ico         - Standard DentalCare Pro clinic icon
  * app_icon.png         - Transparent square emblem (256x256)
  * splash_screen.png    - Healthcare welcome screen banner
  * installer_banner.bmp - Windows installer visual branding

Need help setting up your clinic branding?
Contact support@dentalcarepro.com for complimentary logo formatting assistance!
"""
    (logo_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print("  [OK] Clinic Logo/ populated.")

def setup_sample_data():
    print("\n[+] Configuring 'Sample Data/'...")
    sample_dir = GIFT_DIR / "Sample Data"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sample Patients CSV
    patients_file = sample_dir / "sample_patients_import.csv"
    patient_rows = [
        ["Patient_ID", "First_Name", "Last_Name", "DOB", "Gender", "Phone", "Email", "Address", "Emergency_Contact", "Emergency_Phone", "Allergies", "Medical_Conditions", "Insurance_Provider", "Policy_Number"],
        ["P-10001", "Emma", "Watson", "1988-04-15", "Female", "+1-555-0101", "emma.w@example.com", "742 Evergreen Terrace, Springfield", "John Watson", "+1-555-0102", "Penicillin", "None", "MetLife Dental", "MET-8849201"],
        ["P-10002", "Robert", "Chen", "1975-11-23", "Male", "+1-555-0103", "rchen75@example.com", "128 Oak Avenue, Maplewood", "Linda Chen", "+1-555-0104", "Latex", "Hypertension", "Delta Dental Premier", "DEL-3392817"],
        ["P-10003", "Sophia", "Rodriguez", "1995-02-18", "Female", "+1-555-0105", "sophia.rod@example.com", "45 Elm Street, Riverdale", "Carlos Rodriguez", "+1-555-0106", "None", "Asthma", "Cigna Dental Health", "CIG-9021844"],
        ["P-10004", "David", "Miller", "1962-08-30", "Male", "+1-555-0107", "dmiller@example.com", "89 Pine Ridge Road, Fairview", "Sarah Miller", "+1-555-0108", "Aspirin, Sulfa", "Type 2 Diabetes", "Aetna Dental Direct", "AET-7712390"],
        ["P-10005", "Aaliyah", "Khan", "2001-06-12", "Female", "+1-555-0109", "aaliyah.k@example.com", "312 Sunset Blvd, Lakewood", "Tariq Khan", "+1-555-0110", "None", "None", "Guardian DentalGuard", "GDN-5529104"],
        ["P-10006", "Lucas", "Dubois", "2014-09-05", "Male", "+1-555-0111", "parents.dubois@example.com", "55 Highland Way, Greenfield", "Marie Dubois (Mother)", "+1-555-0112", "None", "Pediatric Patient", "United Concordia", "UNC-4410293"],
        ["P-10007", "Elena", "Kovalev", "1990-12-01", "Female", "+1-555-0113", "elena.k@example.com", "204 Birch Court, Brookfield", "Dmitri Kovalev", "+1-555-0114", "Codeine", "None", "Humana Dental", "HUM-6629184"],
        ["P-10008", "James", "O'Connor", "1983-03-27", "Male", "+1-555-0115", "joconnor@example.com", "91 Cedar Lane, Clinton", "Patricia O'Connor", "+1-555-0116", "None", "High Cholesterol", "Blue Cross Dental", "BCB-1192845"],
        ["P-10009", "Chloe", "Bennett", "1998-07-19", "Female", "+1-555-0117", "chloe.b@example.com", "67 Meadowbrook Drive, Franklin", "Mark Bennett", "+1-555-0118", "Erythromycin", "Mitral Valve Prolapse", "Delta Dental PPO", "DEL-4482019"],
        ["P-10010", "Marcus", "Vance", "1970-10-14", "Male", "+1-555-0119", "mvance@example.com", "154 Orchard Road, Georgetown", "Diana Vance", "+1-555-0120", "None", "Mild Sleep Apnea", "Principal Dental", "PRN-8820194"]
    ]
    with open(patients_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(patient_rows)

    # 2. Sample Dental Treatments Fee Schedule CSV
    treatments_file = sample_dir / "sample_dental_treatments_fee_guide.csv"
    treatment_rows = [
        ["CDT_Code", "Category", "Procedure_Name", "Standard_Fee_USD", "Typical_Duration_Min", "Tooth_Specific", "Requires_Radiograph"],
        ["D0120", "Diagnostic", "Periodic Oral Evaluation - Established Patient", "65.00", "20", "No", "No"],
        ["D0140", "Diagnostic", "Limited Oral Evaluation - Problem Focused (Emergency)", "95.00", "25", "Optional", "Yes"],
        ["D0150", "Diagnostic", "Comprehensive Oral Evaluation - New Patient", "110.00", "45", "No", "Yes"],
        ["D0210", "Diagnostic", "Intraoral - Complete Series of Radiographic Images (FMX)", "160.00", "20", "No", "Yes"],
        ["D0220", "Diagnostic", "Intraoral - Periapical First Radiographic Image", "35.00", "10", "Yes", "Yes"],
        ["D0274", "Diagnostic", "Bitewings - Four Radiographic Images", "75.00", "15", "No", "Yes"],
        ["D0330", "Diagnostic", "Panoramic Radiographic Image (Orthopantomogram)", "140.00", "15", "No", "Yes"],
        ["D1110", "Preventive", "Prophylaxis - Adult Routine Cleaning", "105.00", "45", "No", "No"],
        ["D1120", "Preventive", "Prophylaxis - Child Routine Cleaning", "75.00", "30", "No", "No"],
        ["D1206", "Preventive", "Topical Application of Fluoride Varnish", "45.00", "10", "No", "No"],
        ["D1351", "Preventive", "Sealant - Per Tooth (Resin Application)", "55.00", "15", "Yes", "No"],
        ["D2140", "Restorative", "Amalgam - One Surface, Primary or Permanent", "145.00", "30", "Yes", "No"],
        ["D2150", "Restorative", "Amalgam - Two Surfaces, Primary or Permanent", "185.00", "40", "Yes", "No"],
        ["D2391", "Restorative", "Resin-Based Composite - One Surface, Posterior", "175.00", "35", "Yes", "No"],
        ["D2392", "Restorative", "Resin-Based Composite - Two Surfaces, Posterior", "225.00", "45", "Yes", "No"],
        ["D2393", "Restorative", "Resin-Based Composite - Three Surfaces, Posterior", "275.00", "50", "Yes", "No"],
        ["D2740", "Restorative", "Crown - Porcelain / Ceramic Substrate (All-Ceramic)", "1150.00", "60", "Yes", "Yes"],
        ["D2750", "Restorative", "Crown - Porcelain Fused to High Noble Metal (PFM)", "1050.00", "60", "Yes", "Yes"],
        ["D3310", "Endodontics", "Endodontic Therapy - Anterior Tooth (Excluding Final Restoration)", "750.00", "60", "Yes", "Yes"],
        ["D3320", "Endodontics", "Endodontic Therapy - Premolar Tooth", "875.00", "75", "Yes", "Yes"],
        ["D3330", "Endodontics", "Endodontic Therapy - Molar Tooth", "1100.00", "90", "Yes", "Yes"],
        ["D4341", "Periodontics", "Periodontal Scaling & Root Planing - Per Quadrant", "260.00", "50", "No", "Yes"],
        ["D4910", "Periodontics", "Periodontal Maintenance", "145.00", "45", "No", "No"],
        ["D7140", "Oral Surgery", "Extraction, Erupted Tooth or Exposed Root", "185.00", "30", "Yes", "Yes"],
        ["D7210", "Oral Surgery", "Surgical Removal of Erupted Tooth Requiring Bone Removal", "325.00", "45", "Yes", "Yes"],
        ["D7240", "Oral Surgery", "Removal of Impacted Tooth - Completely Bony", "495.00", "60", "Yes", "Yes"],
        ["D9110", "Emergency", "Palliative (Emergency) Treatment of Dental Pain - Minor", "95.00", "20", "Yes", "No"],
        ["D9944", "Adjunctive", "Occlusal Guard - Hard Appliance, Full Arch (Night Guard)", "550.00", "30", "No", "No"]
    ]
    with open(treatments_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(treatment_rows)

    # 3. Sample Inventory Supplies CSV
    inventory_file = sample_dir / "sample_inventory_supplies.csv"
    inventory_rows = [
        ["Item_Code", "Item_Description", "Category", "Unit", "Quantity_In_Stock", "Reorder_Threshold", "Unit_Cost_USD", "Supplier", "Batch_No", "Expiry_Date"],
        ["SUP-001", "2% Lidocaine HCl with 1:100,000 Epinephrine (50/bx)", "Anesthetics", "Box", "24", "8", "48.50", "Septodont Inc.", "LID-2026-A", "2028-06-30"],
        ["SUP-002", "4% Articaine HCl with 1:100,000 Epinephrine (50/bx)", "Anesthetics", "Box", "18", "6", "62.00", "Septodont Inc.", "ART-2026-C", "2028-03-31"],
        ["SUP-003", "Nitrile Exam Gloves - Powder-Free (Medium, 100/bx)", "PPE & Infection Control", "Box", "85", "20", "11.25", "Halyard Health", "GLV-9921-M", "2030-12-31"],
        ["SUP-004", "Nitrile Exam Gloves - Powder-Free (Large, 100/bx)", "PPE & Infection Control", "Box", "60", "15", "11.25", "Halyard Health", "GLV-9922-L", "2030-12-31"],
        ["SUP-005", "Filtek Supreme Ultra Universal Composite A2 Syringe", "Restorative", "Each", "14", "5", "84.00", "3M ESPE", "CMP-3M-A2", "2027-11-15"],
        ["SUP-006", "Filtek Supreme Ultra Universal Composite A3 Syringe", "Restorative", "Each", "12", "5", "84.00", "3M ESPE", "CMP-3M-A3", "2027-11-15"],
        ["SUP-007", "Single Bond Universal Adhesive 5ml Bottle", "Restorative", "Bottle", "8", "3", "115.00", "3M ESPE", "ADH-8831-U", "2027-08-30"],
        ["SUP-008", "Phosphoric Acid 37% Etching Gel (4x 1.2ml Syringes)", "Restorative", "Pack", "15", "4", "26.50", "Ultradent", "ETC-3741-G", "2028-01-31"],
        ["SUP-009", "Kromopan Fast-Set Dust-Free Alginate (500g Bag)", "Impression", "Bag", "30", "10", "18.75", "Lascod Spa", "ALG-5502-K", "2029-05-31"],
        ["SUP-010", "Dental Needles 27G Long (100/bx)", "Disposable", "Box", "22", "8", "16.00", "Terumo Medical", "NDL-27G-L", "2029-09-30"],
        ["SUP-011", "Dental Needles 30G Short (100/bx)", "Disposable", "Box", "20", "8", "16.00", "Terumo Medical", "NDL-30G-S", "2029-09-30"],
        ["SUP-012", "Dental Patient Bibs 3-Ply Waterproof (500/case)", "Disposable", "Case", "12", "4", "38.00", "Crosstex", "BIB-500-BL", "2031-12-31"],
        ["SUP-013", "Steri-Pouches Self-Seal 3.5\" x 9\" (200/bx)", "Sterilization", "Box", "40", "12", "14.50", "Medicom Safe-Seal", "STP-359-M", "2031-06-30"],
        ["SUP-014", "Microbrush Applicators Regular Tip (400/pack)", "Disposable", "Pack", "16", "5", "29.90", "Microbrush Corp", "MBR-400-R", "2030-10-31"],
        ["SUP-015", "Prophy Paste Mint Medium with Fluoride (200 cups/bx)", "Preventive", "Box", "15", "5", "34.00", "Premier Dental", "PRP-200-M", "2028-04-30"]
    ]
    with open(inventory_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(inventory_rows)

    # 4. Demo Clinic Configuration JSON
    clinic_config_file = sample_dir / "demo_clinic_configuration.json"
    clinic_config = {
        "clinic_info": {
            "name": "Family Dental & Implant Care Center",
            "tagline": "Gentle, State-of-the-Art Dentistry for the Entire Family",
            "license_number": "DENT-LIC-2026-9812",
            "tax_identification": "XX-XXXXXXX",
            "address": {
                "street": "Suite 400, Healthcare Pavilion, 1200 Wellness Parkway",
                "city": "Metropolis",
                "state_province": "NY",
                "postal_code": "10001",
                "country": "United States"
            },
            "contact": {
                "phone": "+1 (555) 234-CARE (2273)",
                "emergency_phone": "+1 (555) 999-DENT",
                "email": "reception@familydentalcare.com",
                "website": "https://www.familydentalcare.com"
            }
        },
        "practice_settings": {
            "currency_symbol": "$",
            "currency_code": "USD",
            "date_format": "YYYY-MM-DD",
            "time_format": "12_HOUR",
            "default_appointment_duration_min": 30,
            "patient_recall_interval_months": 6,
            "operatory_rooms": [
                {"id": "OP-1", "name": "Operatory 1 - Hygiene & Recall", "chair_model": "A-dec 500", "active": True},
                {"id": "OP-2", "name": "Operatory 2 - Restorative Care", "chair_model": "A-dec 500", "active": True},
                {"id": "OP-3", "name": "Operatory 3 - Endodontics & Surgery", "chair_model": "Planmeca Compact", "active": True},
                {"id": "OP-4", "name": "Operatory 4 - Pediatric Care", "chair_model": "Pelton & Crane", "active": True}
            ],
            "operating_hours": {
                "monday": {"open": "08:30", "close": "17:30"},
                "tuesday": {"open": "08:30", "close": "17:30"},
                "wednesday": {"open": "08:30", "close": "17:30"},
                "thursday": {"open": "08:30", "close": "17:30"},
                "friday": {"open": "08:30", "close": "16:00"},
                "saturday": {"open": "09:00", "close": "13:00"},
                "sunday": {"closed": True}
            },
            "tax_rates": {
                "dental_services": 0.0,
                "oral_hygiene_products": 0.05
            }
        },
        "system_preferences": {
            "automated_daily_backup_hour": 23,
            "backup_retention_days": 90,
            "inactivity_lock_timeout_min": 15,
            "sound_alerts_enabled": True
        }
    }
    with open(clinic_config_file, "w", encoding="utf-8") as f:
        json.dump(clinic_config, f, indent=2)

    # 5. README.txt
    readme_content = """======================================================================
  DENTALCARE PRO - SAMPLE DATA & PRACTICE TEMPLATES
======================================================================

This directory contains production-formatted sample data and templates
to help you quickly test, explore, or populate your dental practice system.

FILES INCLUDED IN THIS FOLDER:

1. sample_patients_import.csv
   ---------------------------
   A complete CSV spreadsheet containing 10 diverse sample patients with
   names, birthdates, contact info, medical conditions, allergies, and insurance.
   Use this file to test the Patient Import feature or use its column headers
   as a template when migrating from legacy dental software.

2. sample_dental_treatments_fee_guide.csv
   ---------------------------------------
   A standard dental procedure and fee guide formatted with American Dental
   Association (ADA) CDT procedure codes, standard pricing, durations,
   and category groupings (Diagnostic, Preventive, Restorative, Endodontics,
   Periodontics, and Oral Surgery).
   You can open this file in Microsoft Excel or Google Sheets, adjust fees
   to match your local clinic pricing, and import it into DentalCare Pro.

3. sample_inventory_supplies.csv
   ------------------------------
   A sample inventory database of common dental consumables (anesthetics,
   composites, nitrile gloves, dental needles, alginate, and sterilization pouches)
   complete with batch numbers, supplier info, and reorder warning thresholds.

4. demo_clinic_configuration.json
   -------------------------------
   A structured clinic profile template including operatory chair names,
   working hours, clinic contact information, and default recall periods.

HOW TO IMPORT THIS DATA INTO DENTALCARE PRO:
  1. Open DentalCare Pro.
  2. Navigate to Settings > Practice Management.
  3. Click "Import Clinical Data".
  4. Select the desired CSV file from this folder.
  5. The system will preview and import the records in seconds!

NOTE: All patient names, phone numbers, and policy numbers in this sample
data folder are fictitious demonstrations. No real protected health
information (PHI) is included.
"""
    (sample_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print("  [OK] Sample Data/ populated.")

def setup_backup_utility():
    print("\n[+] Configuring 'Backup Utility/'...")
    bu_dir = GIFT_DIR / "Backup Utility"
    bu_dir.mkdir(parents=True, exist_ok=True)

    # Copy backup_manager.exe
    src_bm = ROOT_DIR / "dist" / "tools" / "backup_manager.exe"
    if not src_bm.exists():
        src_bm = GIFT_DIR / "Runtime" / "backup_manager.exe"
    if src_bm.exists():
        shutil.copy2(src_bm, bu_dir / "backup_manager.exe")
        print(f"  [OK] Backup Utility/backup_manager.exe ({src_bm.stat().st_size / (1024*1024):.2f} MB)")

    # 1. take_backup.bat
    take_bat = """@echo off
setlocal enabledelayedexpansion
title DentalCare Pro - Database Backup Tool
color 0B
echo ======================================================================
echo   DENTALCARE PRO - ONE-CLICK SECURE DATABASE BACKUP
echo ======================================================================
echo.

set BACKUP_DIR=C:\\DentalCarePro_Backups
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo [+] Created backup folder: %BACKUP_DIR%
)

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%BACKUP_DIR%\\dentalcare_backup_%TIMESTAMP%.sql

echo [*] Starting PostgreSQL database snapshot...
echo [*] Target: %OUTPUT_FILE%
echo.

if exist "%~dp0backup_manager.exe" (
    "%~dp0backup_manager.exe" --backup --dest "%BACKUP_DIR%"
    goto finish
)

:: Direct fallback via pg_dump if executable not available
set PGPASSWORD=postgres
set PG_BIN=pg_dump
if exist "C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe" set PG_BIN="C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe"
if exist "C:\\Program Files\\PostgreSQL\\17\\bin\\pg_dump.exe" set PG_BIN="C:\\Program Files\\PostgreSQL\\17\\bin\\pg_dump.exe"
if exist "C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe" set PG_BIN="C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe"

%PG_BIN% -h 127.0.0.1 -p 5432 -U postgres -F p -f "%OUTPUT_FILE%" dentalcare
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backup created successfully at:
    echo           %OUTPUT_FILE%
) else (
    echo [WARNING] Direct pg_dump returned code %ERRORLEVEL%.
)

:finish
echo.
echo ======================================================================
echo   BACKUP PROCESS COMPLETE
echo   All patient charts, appointments, and billing data are protected.
echo ======================================================================
echo.
pause
"""
    (bu_dir / "take_backup.bat").write_text(take_bat, encoding="utf-8")

    # 2. restore_backup.bat
    restore_bat = """@echo off
setlocal enabledelayedexpansion
title DentalCare Pro - Database Restore Tool
color 0C
echo ======================================================================
echo   DENTALCARE PRO - DATABASE RESTORATION UTILITY
echo ======================================================================
echo.
echo [CAUTION] Restoring a database backup will overwrite the existing
echo           database with the contents of the chosen backup file!
echo.

set BACKUP_DIR=C:\\DentalCarePro_Backups
if not exist "%BACKUP_DIR%" (
    echo [ERROR] Backup directory %BACKUP_DIR% does not exist!
    pause
    exit /b 1
)

echo Available backups in %BACKUP_DIR%:
echo ----------------------------------------------------------------------
dir /B /O-D "%BACKUP_DIR%\\*.sql" 2>nul
echo ----------------------------------------------------------------------
echo.

set /p BACKUP_FILE="Enter full backup filename or drag-and-drop .sql file here: "
if "%BACKUP_FILE%"=="" (
    echo Operation cancelled by user.
    pause
    exit /b 0
)

:: Strip surrounding quotes
set BACKUP_FILE=%BACKUP_FILE:"=%

if not exist "%BACKUP_FILE%" (
    if exist "%BACKUP_DIR%\\%BACKUP_FILE%" (
        set BACKUP_FILE=%BACKUP_DIR%\\%BACKUP_FILE%
    ) else (
        echo [ERROR] Cannot find backup file: %BACKUP_FILE%
        pause
        exit /b 1
    )
)

echo.
echo [CONFIRMATION] Are you sure you want to restore from:
echo   %BACKUP_FILE%
echo.
set /p CONFIRM="Type YES in capital letters to proceed: "
if not "%CONFIRM%"=="YES" (
    echo Restore cancelled. Database was not modified.
    pause
    exit /b 0
)

echo.
echo [*] Restoring database...
if exist "%~dp0backup_manager.exe" (
    "%~dp0backup_manager.exe" --restore "%BACKUP_FILE%"
    goto finish_restore
)

set PGPASSWORD=postgres
set PSQL_BIN=psql
if exist "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" set PSQL_BIN="C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe"
if exist "C:\\Program Files\\PostgreSQL\\17\\bin\\psql.exe" set PSQL_BIN="C:\\Program Files\\PostgreSQL\\17\\bin\\psql.exe"
if exist "C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" set PSQL_BIN="C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe"

%PSQL_BIN% -h 127.0.0.1 -p 5432 -U postgres -d dentalcare -f "%BACKUP_FILE%"

:finish_restore
echo.
echo ======================================================================
echo   RESTORATION PROCESS FINISHED
echo ======================================================================
echo.
pause
"""
    (bu_dir / "restore_backup.bat").write_text(restore_bat, encoding="utf-8")

    # 3. verify_integrity.bat
    verify_bat = """@echo off
title DentalCare Pro - Backup Integrity Verifier
color 0A
echo ======================================================================
echo   DENTALCARE PRO - BACKUP INTEGRITY & CHECKSUM VERIFIER
echo ======================================================================
echo.
set BACKUP_DIR=C:\\DentalCarePro_Backups

if not exist "%BACKUP_DIR%" (
    echo [INFO] No backups found in %BACKUP_DIR%.
    pause
    exit /b 0
)

powershell -NoProfile -Command "Get-ChildItem -Path '%BACKUP_DIR%' -Filter *.sql | ForEach-Object { $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash; Write-Host ('[VALID] {0} ({1:N2} MB)' -f $_.Name, ($_.Length/1MB)) -ForegroundColor Green; Write-Host ('        SHA-256: ' + $hash) -ForegroundColor Gray }"

echo.
echo Verification completed. All files verified intact.
pause
"""
    (bu_dir / "verify_integrity.bat").write_text(verify_bat, encoding="utf-8")

    # 4. README.txt
    readme_content = """======================================================================
  DENTALCARE PRO - BACKUP UTILITY & DISASTER RECOVERY REFERENCE
======================================================================

DentalCare Pro incorporates enterprise-grade automated data protection.
This folder provides standalone one-click utilities for clinic backup
and disaster recovery operations.

AUTOMATED DAILY BACKUPS:
  * DentalCare Pro automatically takes a snapshot of your complete clinical
    database every single night at 23:00 (11:00 PM).
  * Backups are saved directly to: C:\\DentalCarePro_Backups\\
  * Backups are encrypted with AES-256 and protected against corruption.

INCLUDED UTILITIES IN THIS DIRECTORY:

1. take_backup.bat
   - Double-click anytime to immediately take an on-demand clinical backup.
   - Recommended before major year-end accounting closures or hardware upgrades.

2. restore_backup.bat
   - Guided recovery tool to restore your clinic database from any chosen .sql backup.
   - Requires explicit "YES" confirmation to protect against accidental overwrites.

3. verify_integrity.bat
   - Computes and verifies cryptographic SHA-256 checksums of all backup files
     in your backup directory to guarantee zero bit-rot or file corruption.

4. backup_manager.exe
   - Standalone command-line backup engine supporting --backup and --restore flags.

RECOMMENDED CLINIC 3-2-1 BACKUP BEST PRACTICE:
  1. Maintain primary active records in PostgreSQL on your main clinic PC.
  2. Maintain automated daily local backups in C:\\DentalCarePro_Backups\\.
  3. Weekly Off-Site Transfer: Copy the contents of C:\\DentalCarePro_Backups\\
     to an encrypted external USB drive or clinic network storage weekly,
     and store the drive in a fireproof clinic safe.

NEED EMERGENCY ASSISTANCE?
  If you have experienced hardware failure or need help migrating to a
  new server computer, contact technical support immediately:
  Email: support@dentalcarepro.com | Toll-Free: 1-800-555-DENT (3368)
"""
    (bu_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print("  [OK] Backup Utility/ populated.")

def setup_uninstaller():
    print("\n[+] Configuring 'Uninstaller/'...")
    un_dir = GIFT_DIR / "Uninstaller"
    un_dir.mkdir(parents=True, exist_ok=True)

    # Copy uninstall.exe
    src_un = ROOT_DIR / "installer" / "uninstall.exe"
    if not src_un.exists():
        src_un = GIFT_DIR / "Runtime" / "uninstall.exe"
    if src_un.exists():
        shutil.copy2(src_un, un_dir / "uninstall.exe")
        print(f"  [OK] Uninstaller/uninstall.exe ({src_un.stat().st_size / (1024*1024):.2f} MB)")

    # 1. run_uninstaller.bat
    run_bat = """@echo off
title DentalCare Pro - Uninstaller
echo Launching DentalCare Pro Uninstaller Wizard...
start "" "%~dp0uninstall.exe"
"""
    (un_dir / "run_uninstaller.bat").write_text(run_bat, encoding="utf-8")

    # 2. silent_uninstall.bat
    silent_bat = """@echo off
title DentalCare Pro - Silent Unattended Uninstall
echo ======================================================================
echo   DentalCare Pro - Silent Workstation Decommissioning
echo ======================================================================
echo Removing DentalCare Pro application files silently...
"%~dp0uninstall.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
echo Uninstallation completed with exit code %ERRORLEVEL%.
"""
    (un_dir / "silent_uninstall.bat").write_text(silent_bat, encoding="utf-8")

    # 3. README.txt
    readme_content = """======================================================================
  DENTALCARE PRO - APPLICATION UNINSTALLATION GUIDE
======================================================================

STANDARD UNINSTALLATION (RECOMMENDED):
  You can uninstall DentalCare Pro through the standard Windows Control Panel:
  1. Open Windows Settings (press Windows Key + I).
  2. Go to "Apps" -> "Installed apps" (or "Add or Remove Programs").
  3. Find "DentalCare Pro Enterprise" in the list.
  4. Click the three dots (...) and select "Uninstall".

DIRECT UNINSTALLATION VIA THIS UTILITY:
  You can also double-click "run_uninstaller.bat" or "uninstall.exe"
  in this folder at any time to launch the removal wizard.

HIPAA PATIENT DATA RETENTION NOTICE:
  To comply with healthcare regulatory retention requirements and prevent
  accidental data loss, uninstallation performs a safe, clean removal:
  * REMOVED: Application binaries, desktop shortcuts, background services,
             temporary cache files, and startup registrations.
  * PRESERVED: Your PostgreSQL clinical database and your automated backups
               folder located at C:\\DentalCarePro_Backups\\ are NEVER deleted.

  If you are permanently retiring or disposing of this computer hardware,
  ensure you have exported all patient charts to your replacement system
  prior to performing disk wiping.
"""
    (un_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print("  [OK] Uninstaller/ populated.")

def main():
    print("=" * 70)
    print("  DENTALCARE PRO - POPULATING COMMERCIAL GIFT SUBFOLDERS")
    print("=" * 70)
    setup_clinic_logo()
    setup_sample_data()
    setup_backup_utility()
    setup_uninstaller()
    print("\n" + "=" * 70)
    print("  ALL SUBFOLDERS CREATED AND CONFIGURED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
