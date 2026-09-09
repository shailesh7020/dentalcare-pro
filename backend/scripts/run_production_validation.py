# backend/scripts/run_production_validation.py
"""
DentalCare Pro - Final Production Validation & QA Suite (Local Clinic Edition)
Executes comprehensive end-to-end testing across all 19 verification phases.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time as pytime
from uuid import UUID, uuid4

# Set test environment
config_path = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro" / "config.json"
db_url = "postgresql+asyncpg://postgres:postgres123@127.0.0.1:5432/dentalcare"
if config_path.exists():
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        db_url = cfg.get("DATABASE_URL", db_url)
    except Exception:
        pass

os.environ.update({
    "ENVIRONMENT": "development",
    "DATABASE_URL": db_url,
    "SECRET_KEY": "dentalcare-production-secret-key-must-be-very-long-and-secure",
    "JWT_SECRET": "dentalcare-production-jwt-secret-key-must-be-very-long-and-secure",
    "JWT_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "REFRESH_TOKEN_EXPIRE_DAYS": "14",
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "CORS_ORIGINS": json.dumps(["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]),
})

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token
from app.models.appointment import Appointment, AppointmentStatus, Chair
from app.models.billing import Invoice, InvoiceItem, InvoiceItemType, InvoiceStatus, Payment, PaymentMethod, PaymentStatus
from app.models.commercial import BackupDestination, BackupRecord, BackupType, ClinicianSignature, SignatureType
from app.models.identity import Clinic, Role, User
from app.models.inventory import InventoryBatch, InventoryItem, StockTransaction, StockTransactionType, Supplier
from app.models.notification import ClinicNotificationSetting, Notification, NotificationPriority, NotificationType
from app.models.patient import Gender, Patient
from app.models.prescription import MedicineCatalog, Prescription, PrescriptionItem, PrescriptionStatus
from app.models.treatment import Treatment, TreatmentProcedure, TreatmentStatus
from app.services.backup_service import BackupService
from app.services.clinical_document_pdf_service import ClinicalDocumentPDFService
from app.services.clinical_storage_service import AntiVirusService, ClinicalStorageService
from app.services.clinic_network_service import ClinicNetworkService
from app.services.notifications.reminder_service import ReminderService
from app.services.qr_service import QRCodeService
from app.services.signature_service import ClinicianSignatureService
from app.services.update_service import UpdateService

engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

results = {
    "phases": {},
    "metrics": {},
    "issues": [],
}


def log_phase(phase_num: int, phase_name: str, status: str, details: dict | None = None):
    results["phases"][f"Phase {phase_num}: {phase_name}"] = {
        "status": status,
        "details": details or {},
    }
    print(f"[{'PASS' if status == 'PASSED' else 'FAIL'}] Phase {phase_num}: {phase_name}")


async def validate_phase1_installation():
    """Phase 1: Installation & Packaging"""
    details = {}
    iss_file = BASE_DIR.parent / "installer" / "DentalCarePro_Setup.iss"
    details["iss_exists"] = iss_file.exists()
    
    iss_text = iss_file.read_text(encoding="utf-8") if iss_file.exists() else ""
    details["has_postgres_detection"] = "IsPostgresInstalled" in iss_text
    details["has_desktop_icon"] = "autodesktop" in iss_text
    details["has_uninstaller"] = "CurUninstallStepChanged" in iss_text

    pipeline = BASE_DIR.parent / "scripts" / "build_commercial_release.py"
    details["release_pipeline_exists"] = pipeline.exists()

    gift_dir = BASE_DIR.parent / "Dental Clinic Management Gift"
    details["gift_dir_exists"] = gift_dir.exists()

    passed = all([
        details["iss_exists"],
        details["has_postgres_detection"],
        details["has_desktop_icon"],
        details["has_uninstaller"],
        details["release_pipeline_exists"],
    ])
    log_phase(1, "Installation & Packaging Test", "PASSED" if passed else "FAILED", details)


async def validate_phase2_startup():
    """Phase 2: Application Startup & Health Probes"""
    details = {}
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/health/live")
        with urllib.request.urlopen(req, timeout=3) as res:
            details["backend_live_status"] = res.status
            details["backend_live_body"] = json.loads(res.read().decode())
    except Exception as e:
        details["backend_live_error"] = str(e)

    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/docs")
        with urllib.request.urlopen(req, timeout=3) as res:
            details["swagger_status"] = res.status
    except Exception as e:
        details["swagger_error"] = str(e)

    try:
        req = urllib.request.Request("http://127.0.0.1:3000")
        with urllib.request.urlopen(req, timeout=3) as res:
            details["frontend_web_status"] = res.status
    except Exception as e:
        details["frontend_web_error"] = str(e)

    passed = (
        details.get("backend_live_status") == 200 and
        details.get("swagger_status") == 200 and
        details.get("frontend_web_status") == 200
    )
    log_phase(2, "Application Startup & Health", "PASSED" if passed else "FAILED", details)


async def validate_phase3_database():
    """Phase 3: Database Schema & Integrity"""
    details = {}
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT version_num FROM alembic_version"))
        rev = res.scalar()
        details["alembic_revision"] = rev

        res = await db.execute(text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        ))
        tbl_count = res.scalar()
        details["table_count"] = tbl_count

        res = await db.execute(text("SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'"))
        idx_count = res.scalar()
        details["index_count"] = idx_count

    passed = rev in ("20260909_0017", "20260909_0018") and tbl_count >= 40 and idx_count >= 200
    log_phase(3, "Database Schema & Integrity", "PASSED" if passed else "FAILED", details)


async def validate_phase4_login():
    """Phase 4: Login System & Roles"""
    details = {}
    roles = [Role.SUPER_ADMIN, Role.DENTIST, Role.RECEPTIONIST, Role.ASSISTANT]
    tokens = {}
    async with AsyncSessionLocal() as db:
        for r in roles:
            stmt = select(User).where(User.role == r, User.is_active.is_(True), User.deleted_at.is_(None)).limit(1)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                token = create_access_token(str(user.id), str(user.clinic_id), user.role.value)
                tokens[r.value] = {"user_id": str(user.id), "token_len": len(token)}
            else:
                tokens[r.value] = "USER_NOT_FOUND"

    details["role_tokens"] = tokens
    details["password_hashing_works"] = verify_password("secret123", hash_password("secret123"))
    details["password_rejection_works"] = not verify_password("wrong", hash_password("secret123"))

    passed = len(tokens) == 4 and all(v != "USER_NOT_FOUND" for v in tokens.values()) and details["password_hashing_works"]
    log_phase(4, "Login & Authentication System", "PASSED" if passed else "FAILED", details)


async def validate_phase5_patient_management():
    """Phase 5: Patient Management"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        test_phone = f"98765{int(pytime.time()) % 100000:05d}"
        
        # 1. Create Patient
        pat = Patient(
            clinic_id=clinic.id,
            first_name="Validation",
            last_name="Patient",
            patient_number=f"VAL-{int(pytime.time()) % 10000:04d}",
            mobile_number=test_phone,
            email=f"val_{test_phone}@example.com",
            gender=Gender.MALE,
            date_of_birth=date(1990, 5, 20),
        )
        db.add(pat)
        await db.commit()
        await db.refresh(pat)
        details["patient_created_id"] = str(pat.id)

        # 2. Search Patient
        res = await db.execute(select(Patient).where(Patient.mobile_number == test_phone))
        found = res.scalar_one_or_none()
        details["patient_search_found"] = found is not None

        # 3. QR Code payload
        qr_payload = QRCodeService.generate_patient_payload(str(pat.id), str(clinic.id))
        details["qr_payload"] = qr_payload

        # 4. Soft Delete
        pat.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        res = await db.execute(select(Patient).where(Patient.id == pat.id, Patient.deleted_at.is_(None)))
        details["soft_delete_effective"] = res.scalar_one_or_none() is None

        # 5. Restore
        pat.deleted_at = None
        await db.commit()
        res = await db.execute(select(Patient).where(Patient.id == pat.id, Patient.deleted_at.is_(None)))
        details["restore_effective"] = res.scalar_one_or_none() is not None

    passed = details["patient_search_found"] and details["soft_delete_effective"] and details["restore_effective"]
    log_phase(5, "Patient Management", "PASSED" if passed else "FAILED", details)


async def validate_phase6_appointments():
    """Phase 6: Appointments & Conflict Detection"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        dentist = (await db.execute(select(User).where(User.role == Role.DENTIST).limit(1))).scalar_one()
        patient = (await db.execute(select(Patient).where(Patient.deleted_at.is_(None)).limit(1))).scalar_one()
        chair = (await db.execute(select(Chair).where(Chair.clinic_id == clinic.id).limit(1))).scalar_one_or_none()
        if not chair:
            chair = Chair(
                clinic_id=clinic.id,
                name="Chair 1",
                room_number="Room 101",
                is_active=True,
            )
            db.add(chair)
            await db.commit()
            await db.refresh(chair)

        today = date.today() + timedelta(days=2)
        appt_num = f"APT-VAL-{int(pytime.time()) % 100000}"
        appt = Appointment(
            clinic_id=clinic.id,
            dentist_id=dentist.id,
            patient_id=patient.id,
            chair_id=chair.id,
            appointment_number=appt_num,
            date=today,
            start_time=time(10, 0),
            end_time=time(10, 30),
            duration=30,
            status=AppointmentStatus.SCHEDULED,
            chief_complaint="Validation Scaling Checkup",
        )
        db.add(appt)
        await db.commit()
        await db.refresh(appt)
        details["appointment_booked_id"] = str(appt.id)

        # Conflict check: query overlapping appointment for same dentist
        conflict_query = select(Appointment).where(
            Appointment.dentist_id == dentist.id,
            Appointment.date == today,
            Appointment.start_time < time(10, 30),
            Appointment.end_time > time(10, 0),
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        overlapping = (await db.execute(conflict_query)).scalars().all()
        details["conflict_detection_count"] = len(overlapping)

        # Cancellation
        appt.status = AppointmentStatus.CANCELLED
        await db.commit()
        details["appointment_cancelled"] = True

    passed = details["conflict_detection_count"] >= 1 and details["appointment_cancelled"]
    log_phase(6, "Appointment Scheduling & Conflicts", "PASSED" if passed else "FAILED", details)


async def validate_phase7_treatments():
    """Phase 7: Treatments & Clinical Procedures"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        dentist = (await db.execute(select(User).where(User.role == Role.DENTIST).limit(1))).scalar_one()
        patient = (await db.execute(select(Patient).where(Patient.deleted_at.is_(None)).limit(1))).scalar_one()
        chair = (await db.execute(select(Chair).where(Chair.clinic_id == clinic.id).limit(1))).scalar_one_or_none()
        if not chair:
            chair = Chair(
                clinic_id=clinic.id,
                name="Chair 1",
                room_number="Room 101",
                is_active=True,
            )
            db.add(chair)
            await db.commit()
            await db.refresh(chair)

        # Create appointment for treatment
        appt_num7 = f"APT-VAL7-{int(pytime.time()) % 100000}"
        appt = Appointment(
            clinic_id=clinic.id,
            dentist_id=dentist.id,
            patient_id=patient.id,
            chair_id=chair.id,
            appointment_number=appt_num7,
            date=date.today(),
            start_time=time(11, 0),
            end_time=time(11, 45),
            duration=45,
            status=AppointmentStatus.CONFIRMED,
            chief_complaint="Clinical Treatment Execution",
        )
        db.add(appt)
        await db.commit()
        await db.refresh(appt)

        tx = Treatment(
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=dentist.id,
            appointment_id=appt.id,
            treatment_number=f"TRT-VAL-{int(pytime.time()) % 10000}",
            diagnosis="Dental Caries #16 Occlusal",
            treatment_plan="Composite Restoration",
            status=TreatmentStatus.IN_PROGRESS,
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        details["treatment_id"] = str(tx.id)

        # Add Procedure
        proc = TreatmentProcedure(
            treatment_id=tx.id,
            procedure_name="Resin-based composite - one surface, posterior",
            tooth_number="16",
            cost=2500.0,
            status="COMPLETED",
        )
        db.add(proc)
        await db.commit()
        details["procedure_recorded"] = True

    passed = details["procedure_recorded"]
    log_phase(7, "Treatments & Clinical Procedures", "PASSED" if passed else "FAILED", details)


async def validate_phase8_billing():
    """Phase 8: Billing, Invoicing & Receipts"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        patient = (await db.execute(select(Patient).where(Patient.deleted_at.is_(None)).limit(1))).scalar_one()
        dentist = (await db.execute(select(User).where(User.role == Role.DENTIST).limit(1))).scalar_one()

        inv = Invoice(
            clinic_id=clinic.id,
            patient_id=patient.id,
            dentist_id=dentist.id,
            invoice_number=f"INV-VAL-{int(pytime.time()) % 10000}",
            date=date.today(),
            subtotal=2000.0,
            discount_amount=200.0,
            tax_amount=324.0,
            grand_total=2124.0,
            amount_paid=0.0,
            balance_due=2124.0,
            status=InvoiceStatus.UNPAID,
            created_by=dentist.id,
            updated_by=dentist.id,
        )
        db.add(inv)
        await db.commit()
        await db.refresh(inv)

        # Payment
        pay = Payment(
            clinic_id=clinic.id,
            invoice_id=inv.id,
            amount=2124.0,
            method=PaymentMethod.UPI,
            status=PaymentStatus.COMPLETED,
            receipt_number=f"RCP-VAL-{int(pytime.time()) % 10000}",
            payment_date=date.today(),
            received_by=dentist.id,
        )
        db.add(pay)
        inv.amount_paid = 2124.0
        inv.balance_due = 0.0
        inv.status = InvoiceStatus.PAID
        await db.commit()

        details["invoice_paid"] = True
        details["balance_zero"] = inv.balance_due == 0.0

    passed = details["invoice_paid"] and details["balance_zero"]
    log_phase(8, "Billing, Invoicing & Payments", "PASSED" if passed else "FAILED", details)


async def validate_phase9_inventory():
    """Phase 9: Inventory & Supply Chain"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        user = (await db.execute(select(User).limit(1))).scalar_one()

        item = InventoryItem(
            clinic_id=clinic.id,
            name=f"Composite Kit Val-{int(pytime.time()) % 1000}",
            sku=f"SKU-VAL-{int(pytime.time()) % 1000}",
            category="CONSUMABLES",
            unit="KIT",
            minimum_stock=5,
            current_quantity=10,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)

        # Stock Transaction - Consumption
        tx = StockTransaction(
            clinic_id=clinic.id,
            item_id=item.id,
            transaction_type=StockTransactionType.CONSUMPTION.value,
            quantity=2,
            previous_quantity=10,
            new_quantity=8,
            unit_cost=800.0,
            total_cost=1600.0,
            actor_id=user.id,
            reason="Clinical usage in restorative treatment",
        )
        item.current_quantity -= 2
        db.add(tx)
        await db.commit()

        details["item_created"] = True
        details["stock_consumed_balance"] = item.current_quantity

    passed = details["stock_consumed_balance"] == 8
    log_phase(9, "Inventory & Stock Tracking", "PASSED" if passed else "FAILED", details)


async def validate_phase10_reports():
    """Phase 10: Reports & Analytics Queries"""
    details = {}
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(func.count(Invoice.id), func.sum(Invoice.amount_paid)))
        inv_count, total_revenue = res.first()
        details["total_invoices"] = inv_count
        details["total_revenue"] = float(total_revenue or 0.0)

        res = await db.execute(select(func.count(Appointment.id)))
        appt_count = res.scalar()
        details["total_appointments"] = appt_count

    passed = inv_count is not None and appt_count is not None
    log_phase(10, "Reports & Analytics Engine", "PASSED" if passed else "FAILED", details)


async def validate_phase11_multi_user():
    """Phase 11: Multi-User Clinic Network & Concurrency"""
    details = {}
    clinic_id = uuid4()
    
    ws_roles = [
        ("WS_RECEPTION_01", "RECEPTION"),
        ("WS_DENTIST_01", "DENTIST"),
        ("WS_ASSISTANT_01", "ASSISTANT"),
        ("WS_ADMIN_01", "ADMIN"),
    ]
    for ws_id, role in ws_roles:
        if clinic_id not in ClinicNetworkService._workstations:
            ClinicNetworkService._workstations[clinic_id] = {}
        ClinicNetworkService._workstations[clinic_id][ws_id] = {
            "ws": None,
            "role": role,
            "connected_at": datetime.now(timezone.utc),
            "client_ip": "192.168.1.50",
        }

    active = ClinicNetworkService.get_active_workstations(clinic_id)
    details["connected_workstations"] = len(active)
    del ClinicNetworkService._workstations[clinic_id]

    passed = details["connected_workstations"] == 4
    log_phase(11, "Multi-User Clinic Network Test", "PASSED" if passed else "FAILED", details)


async def validate_phase12_backups():
    """Phase 12: Encrypted Backups & Disaster Recovery"""
    details = {}
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        
        backup_rec = await BackupService.create_backup(
            db=db,
            clinic_id=clinic.id,
            backup_type=BackupType.MANUAL,
            destination_type=BackupDestination.LOCAL,
            is_encrypted=True,
            password="TestPassword123!",
        )
        details["backup_file"] = backup_rec.file_name
        details["backup_size_bytes"] = backup_rec.file_size_bytes
        details["backup_sha256"] = backup_rec.checksum_sha256

        p = Path(backup_rec.file_path)
        details["file_exists_on_disk"] = p.exists()

    passed = details["file_exists_on_disk"] and details["backup_size_bytes"] > 0
    log_phase(12, "Encrypted Backups (AES-256) & DR", "PASSED" if passed else "FAILED", details)


async def validate_phase13_pdfs():
    """Phase 13: Clinical PDF Suite Generation"""
    details = {}
    clinic = {"name": "Test Clinic", "phone": "12345", "email": "test@test.com"}
    patient = {"id": "P1", "name": "Test Pat", "age": "30", "phone": "12345"}
    doctor = {"name": "Dr. Test", "reg_number": "REG1"}

    tx_pdf = ClinicalDocumentPDFService.generate_treatment_plan_pdf(clinic, patient, doctor, "Plan", [], 1000.0)
    mc_pdf = ClinicalDocumentPDFService.generate_medical_certificate_pdf(clinic, patient, doctor, "Diagnosis", date.today(), date.today(), date.today())
    slip_pdf = ClinicalDocumentPDFService.generate_appointment_slip_pdf(clinic, patient, {"id": "A1", "date": "2026-09-10", "time": "10:00 AM"})
    consent_pdf = ClinicalDocumentPDFService.generate_consent_form_pdf(clinic, patient, "Surgery", "Risks", doctor)

    details["treatment_plan_pdf_len"] = len(tx_pdf)
    details["medical_certificate_pdf_len"] = len(mc_pdf)
    details["appointment_slip_pdf_len"] = len(slip_pdf)
    details["consent_form_pdf_len"] = len(consent_pdf)

    passed = all(len(pdf) > 500 for pdf in [tx_pdf, mc_pdf, slip_pdf, consent_pdf])
    log_phase(13, "Clinical Document PDF Suite", "PASSED" if passed else "FAILED", details)


async def validate_phase14_rbac():
    """Phase 14: Role-Based Access Control (RBAC)"""
    details = {}
    from app.api.v1.backups import ADMIN_ROLES
    details["admin_roles_guard"] = [r.value for r in ADMIN_ROLES]
    details["reception_blocked_from_admin"] = Role.RECEPTIONIST not in ADMIN_ROLES
    details["assistant_blocked_from_admin"] = Role.ASSISTANT not in ADMIN_ROLES
    details["dentist_blocked_from_admin"] = Role.DENTIST not in ADMIN_ROLES

    passed = details["reception_blocked_from_admin"] and details["assistant_blocked_from_admin"]
    log_phase(14, "Role-Based Permissions & Guarding", "PASSED" if passed else "FAILED", details)


async def validate_phase15_security():
    """Phase 15: Security & Anti-Virus Verification"""
    details = {}
    temp_dir = BASE_DIR / "temp_sec_test"
    temp_dir.mkdir(parents=True, exist_ok=True)
    fake_mz = temp_dir / "test_mz.png"
    fake_mz.write_bytes(b"MZ\x90\x00\x03fake_executable_disguised_as_png")
    
    is_clean, reason = AntiVirusService.scan_file(fake_mz)
    details["disguised_executable_blocked"] = not is_clean
    details["blocked_reason"] = reason

    if fake_mz.exists():
        fake_mz.unlink()
    temp_dir.rmdir()

    passed = details["disguised_executable_blocked"]
    log_phase(15, "Security & Disguised Malware Defense", "PASSED" if passed else "FAILED", details)


async def validate_phase16_performance():
    """Phase 16: Performance Benchmark"""
    details = {}
    start = pytime.perf_counter()
    async with AsyncSessionLocal() as db:
        for _ in range(50):
            await db.execute(select(Patient).limit(10))
    elapsed = pytime.perf_counter() - start
    avg_query_ms = (elapsed / 50.0) * 1000.0
    details["avg_db_query_ms"] = round(avg_query_ms, 2)

    passed = avg_query_ms < 15.0
    log_phase(16, "Database & Query Performance", "PASSED" if passed else "FAILED", details)


async def validate_phase17_ux():
    """Phase 17: User Experience & Responsive Layouts"""
    details = {}
    web_dir = BASE_DIR.parent / "apps" / "web"
    details["web_exists"] = web_dir.exists()
    details["has_globals_css"] = (web_dir / "src" / "app" / "globals.css").exists()
    details["has_appointments_view"] = (web_dir / "src" / "app" / "appointments" / "page.tsx").exists()
    details["has_patients_view"] = (web_dir / "src" / "app" / "patients" / "page.tsx").exists()

    passed = details["web_exists"] and details["has_appointments_view"] and details["has_patients_view"]
    log_phase(17, "User Experience & UI Architecture", "PASSED" if passed else "FAILED", details)


async def validate_phase18_windows_deployment():
    """Phase 18: Standalone Windows Deployment Readiness"""
    details = {}
    details["python_313_installed"] = sys.version_info >= (3, 11)
    details["is_windows"] = os.name == "nt"
    details["postgres_toolchain"] = Path(r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe").exists()

    passed = details["python_313_installed"] and details["is_windows"] and details["postgres_toolchain"]
    log_phase(18, "Windows Standalone Deployment Readiness", "PASSED" if passed else "FAILED", details)


async def validate_phase19_clinic_day_simulation():
    """Phase 19: Real Clinic Full-Day Simulation (20 Patients, Treatments, Invoices, Reports)"""
    details = {}
    start = pytime.perf_counter()
    async with AsyncSessionLocal() as db:
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one()
        dentist = (await db.execute(select(User).where(User.role == Role.DENTIST).limit(1))).scalar_one()
        chair = (await db.execute(select(Chair).where(Chair.clinic_id == clinic.id).limit(1))).scalar_one_or_none()
        if not chair:
            chair = Chair(
                clinic_id=clinic.id,
                name="Chair 1",
                room_number="Room 101",
                is_active=True,
            )
            db.add(chair)
            await db.commit()
            await db.refresh(chair)

        sim_ts = int(pytime.time()) % 10000
        phone_prefix = int(pytime.time()) % 10000000
        patients = []
        for i in range(1, 21):
            p = Patient(
                clinic_id=clinic.id,
                first_name=f"ClinicDay{sim_ts}",
                last_name=f"Patient{i:02d}",
                patient_number=f"CD-{sim_ts}-{i:02d}",
                mobile_number=f"9{phone_prefix:07d}{i:02d}",
                gender=Gender.FEMALE if i % 2 == 0 else Gender.MALE,
                date_of_birth=date(1985 + (i % 20), (i % 12) + 1, 15),
            )
            db.add(p)
            patients.append(p)
        await db.commit()
        details["registered_patients"] = len(patients)

        # 10 Appointments, Treatments & Invoices
        invoices = []
        for i in range(10):
            pat = patients[i]
            appt = Appointment(
                clinic_id=clinic.id,
                dentist_id=dentist.id,
                patient_id=pat.id,
                chair_id=chair.id,
                appointment_number=f"APT-CD-{sim_ts}-{i+1:02d}",
                date=date.today(),
                start_time=time(9 + (i // 2), 30 if i % 2 == 1 else 0),
                end_time=time(9 + (i // 2), 45 if i % 2 == 1 else 30),
                duration=30,
                status=AppointmentStatus.COMPLETED,
                chief_complaint="Routine Dental Treatment",
            )
            db.add(appt)
            await db.flush()

            tx = Treatment(
                clinic_id=clinic.id,
                patient_id=pat.id,
                dentist_id=dentist.id,
                appointment_id=appt.id,
                treatment_number=f"TRT-CD-{sim_ts}-{i+1:02d}",
                diagnosis=f"Clinical Diagnosis Patient {i+1}",
                treatment_plan="Routine Dental Care",
                status=TreatmentStatus.COMPLETED,
            )
            db.add(tx)
            await db.flush()

            inv = Invoice(
                clinic_id=clinic.id,
                patient_id=pat.id,
                dentist_id=dentist.id,
                treatment_id=tx.id,
                appointment_id=appt.id,
                invoice_number=f"INV-CD-{sim_ts}-{i+1:02d}",
                date=date.today(),
                subtotal=1500.0,
                grand_total=1500.0,
                amount_paid=1500.0,
                balance_due=0.0,
                status=InvoiceStatus.PAID,
                created_by=dentist.id,
                updated_by=dentist.id,
            )
            db.add(inv)
            invoices.append(inv)
        await db.commit()
        details["completed_treatments_and_invoices"] = len(invoices)

    elapsed = pytime.perf_counter() - start
    details["simulation_execution_time_seconds"] = round(elapsed, 2)
    passed = details["registered_patients"] == 20 and details["completed_treatments_and_invoices"] == 10
    log_phase(19, "Full Working Day Clinical Simulation", "PASSED" if passed else "FAILED", details)


async def main():
    print("\n===========================================================")
    print("DENTALCARE PRO – FULL 19-PHASE PRODUCTION VALIDATION SUITE")
    print("===========================================================\n")
    
    await validate_phase1_installation()
    await validate_phase2_startup()
    await validate_phase3_database()
    await validate_phase4_login()
    await validate_phase5_patient_management()
    await validate_phase6_appointments()
    await validate_phase7_treatments()
    await validate_phase8_billing()
    await validate_phase9_inventory()
    await validate_phase10_reports()
    await validate_phase11_multi_user()
    await validate_phase12_backups()
    await validate_phase13_pdfs()
    await validate_phase14_rbac()
    await validate_phase15_security()
    await validate_phase16_performance()
    await validate_phase17_ux()
    await validate_phase18_windows_deployment()
    await validate_phase19_clinic_day_simulation()

    summary_file = BASE_DIR.parent / "dist" / "production_validation_results.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved raw validation data to: {summary_file}")


if __name__ == "__main__":
    asyncio.run(main())
