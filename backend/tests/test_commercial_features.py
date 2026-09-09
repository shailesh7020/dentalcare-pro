from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.schemas.admin_settings import (
    BackupScheduleSettings,
    ClinicProfileSettings,
    GatewayCredentialsSettings,
    LocalizationSettings,
    ReminderScheduleSettings,
    UnifiedAdminSettings,
    WorkingHoursSettings,
)
from app.services.backup_service import _derive_fernet_key
from app.services.clinic_network_service import ClinicNetworkService
from app.services.clinical_document_pdf_service import ClinicalDocumentPDFService
from app.services.clinical_storage_service import AntiVirusService
from app.services.qr_service import QRCodeService
from app.services.signature_service import ClinicianSignatureService
from app.services.update_service import CURRENT_APP_VERSION, UpdateService


def test_qr_code_payloads():
    p_id = str(uuid4())
    c_id = str(uuid4())
    a_id = str(uuid4())
    inv_id = str(uuid4())
    rx_id = str(uuid4())

    pat_payload = QRCodeService.generate_patient_payload(p_id, c_id)
    assert f"DENTALCARE:PATIENT:{p_id}:{c_id}" == pat_payload

    appt_payload = QRCodeService.generate_appointment_payload(a_id, p_id)
    assert f"DENTALCARE:APPT:{a_id}:{p_id}" == appt_payload

    inv_payload = QRCodeService.generate_invoice_payload(inv_id, 1500.0, "HASH123")
    assert f"DENTALCARE:INV:{inv_id}:1500.0:HASH123" == inv_payload

    rx_payload = QRCodeService.generate_prescription_payload(rx_id, "HASH999")
    assert f"DENTALCARE:RX:{rx_id}:HASH999" == rx_payload


def test_qr_code_renderers():
    payload = "DENTALCARE:TEST:UNIT_TEST"

    # PNG base64
    b64_png = QRCodeService.generate_qr_png_base64(payload)
    assert b64_png.startswith("data:image/png;base64,")

    # Platypus flowable
    flowable = QRCodeService.generate_qr_flowable(payload, size=75.0)
    assert flowable.drawWidth == 75.0
    assert flowable.drawHeight == 75.0

    # Drawing vector flowable
    drawing = QRCodeService.generate_qr_drawing(payload, size=50.0)
    assert drawing.width == 50.0
    assert drawing.height == 50.0

    # Barcode
    bc_drawing = QRCodeService.generate_barcode_drawing("PAT-009988")
    assert bc_drawing.height >= 28.0

    bc_svg = QRCodeService.generate_barcode_svg_base64("PAT-009988")
    assert bc_svg.startswith("data:image/svg+xml;base64,")


def test_clinician_signature_service_helpers():
    uid = uuid4()
    sig_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    h1 = ClinicianSignatureService.calculate_hash(uid, sig_data)
    h2 = ClinicianSignatureService.calculate_hash(uid, sig_data)
    assert h1 == h2
    assert len(h1) == 64

    # Flowable creation
    img = ClinicianSignatureService.create_signature_flowable(sig_data, width=100, height=40)
    assert img is not None
    assert img.drawWidth == 100
    assert img.drawHeight == 40

    # Invalid data handling
    corrupt_img = ClinicianSignatureService.create_signature_flowable("bad_data", width=100, height=40)
    assert corrupt_img is None


def test_clinical_document_pdf_generation():
    clinic = {"name": "Apex Dental Clinic", "phone": "+91 91234 56789", "email": "help@apexdental.in"}
    patient = {"id": "PAT-777", "name": "Alice Smith", "age": "29", "age_gender": "29 / F", "phone": "+91 98765 00000"}
    doctor = {"name": "Dr. Marcus Vance", "reg_number": "REG-554433"}

    # 1. Treatment Plan PDF
    tp_pdf = ClinicalDocumentPDFService.generate_treatment_plan_pdf(
        clinic_info=clinic,
        patient_info=patient,
        doctor_info=doctor,
        plan_title="Orthodontic Aligners & Scaling",
        procedures=[
            {"tooth": "All", "name": "Ultrasonic Scaling & Polishing", "fee": 1500},
            {"tooth": "Maxilla/Mandible", "name": "Clear Aligners 12-Tray", "fee": 65000},
        ],
        total_estimated=66500.0,
    )
    assert tp_pdf.startswith(b"%PDF")
    assert len(tp_pdf) > 1000

    # 2. Medical Certificate PDF
    mc_pdf = ClinicalDocumentPDFService.generate_medical_certificate_pdf(
        clinic_info=clinic,
        patient_info=patient,
        doctor_info=doctor,
        diagnosis="Dry socket post lower right wisdom tooth surgical disimpaction",
        leave_start_date=date(2026, 9, 10),
        leave_end_date=date(2026, 9, 12),
        resume_date=date(2026, 9, 13),
    )
    assert mc_pdf.startswith(b"%PDF")
    assert len(mc_pdf) > 1000

    # 3. Appointment Slip PDF
    slip_pdf = ClinicalDocumentPDFService.generate_appointment_slip_pdf(
        clinic_info=clinic,
        patient_info=patient,
        appointment_info={"id": str(uuid4()), "date": "2026-09-15", "time": "11:00 AM", "dentist_name": doctor["name"], "chair_number": "1", "type": "Checkup"},
    )
    assert slip_pdf.startswith(b"%PDF")
    assert len(slip_pdf) > 1000

    # 4. Consent Form PDF
    consent_pdf = ClinicalDocumentPDFService.generate_consent_form_pdf(
        clinic_info=clinic,
        patient_info=patient,
        procedure_name="Crown Lengthening & Core Build-up",
        risks_and_benefits="Mild transient sensitivity, localized gingival inflammation.",
        doctor_info=doctor,
    )
    assert consent_pdf.startswith(b"%PDF")
    assert len(consent_pdf) > 1000


def test_backup_encryption_and_integrity(tmp_path: Path):
    raw_content = b"TEST_SQL_DUMP_DATA_CLINICAL_RECORDS"
    password = "StrongClinicPassword2026!"

    # Derive key
    key = _derive_fernet_key(password)
    fernet = Fernet(key)

    # Encrypt
    encrypted = fernet.encrypt(raw_content)
    checksum = hashlib.sha256(encrypted).hexdigest()

    # Verify integrity
    assert hashlib.sha256(encrypted).hexdigest() == checksum

    # Decrypt
    decrypted = fernet.decrypt(encrypted)
    assert decrypted == raw_content

    # Check that tampered content fails integrity
    tampered = encrypted[:-5] + b"XXXXX"
    assert hashlib.sha256(tampered).hexdigest() != checksum


@pytest.mark.asyncio
async def test_update_service():
    check = await UpdateService.check_for_updates()
    assert check.current_version == CURRENT_APP_VERSION
    assert check.latest_version == CURRENT_APP_VERSION
    assert check.has_update is False

    status = UpdateService.get_status()
    assert status.status in ["IDLE", "READY", "CHECKING"]


def test_antivirus_heuristics(tmp_path: Path):
    # Test clean file
    clean_file = tmp_path / "clean_photo.jpg"
    clean_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
    is_clean, msg = AntiVirusService.scan_file(clean_file)
    assert is_clean is True

    # Test dangerous file with MZ executable header
    malicious_file = tmp_path / "trojan_disguised.jpg"
    malicious_file.write_bytes(b"MZ\x90\x00\x03\x00" + b"\x00" * 50)
    is_clean, msg = AntiVirusService.scan_file(malicious_file)
    assert is_clean is False
    assert "executable binary payload" in msg


def test_clinic_network_workstation_tracking():
    clinic_id = uuid4()
    ws_list = ClinicNetworkService.get_active_workstations(clinic_id)
    assert isinstance(ws_list, list)


def test_unified_admin_settings_schema():
    profile = ClinicProfileSettings(
        name="Global Dental Hospital",
        email="info@globaldental.com",
        phone="+91 80 2345 6789",
        currency="INR",
        tax_id_gst="29AAAAA0000A1Z5",
    )
    wh = WorkingHoursSettings(total_chairs=5)
    backup_s = BackupScheduleSettings(retention_days=45)
    reminders = ReminderScheduleSettings(enable_whatsapp=True)
    gateways = GatewayCredentialsSettings(smtp_port=465)
    loc = LocalizationSettings(timezone="Asia/Kolkata")

    settings = UnifiedAdminSettings(
        clinic_profile=profile,
        working_hours=wh,
        backup_schedule=backup_s,
        reminder_schedule=reminders,
        gateways=gateways,
        localization=loc,
    )

    data = settings.model_dump()
    assert data["clinic_profile"]["name"] == "Global Dental Hospital"
    assert data["working_hours"]["total_chairs"] == 5
    assert data["backup_schedule"]["retention_days"] == 45
    assert data["reminder_schedule"]["enable_whatsapp"] is True
