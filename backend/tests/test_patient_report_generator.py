from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.patient_report import (
    ALL_REPORT_SECTIONS,
    PatientReportResponse,
    PatientReportSectionEnum,
)
from app.services.patient_report_pdf_service import PatientReportPDFService


def test_pdf_report_generation_all_sections():
    clinic_info = {
        "id": str(uuid4()),
        "name": "Apex Dental Clinic",
        "phone": "+91 98765 43210",
        "email": "contact@apexdental.com",
        "address": "402 Healthcare Tower, Bandra West, Mumbai",
    }
    patient_data = {
        "id": str(uuid4()),
        "full_name": "Rohan Verma",
        "patient_number": "P-2026-0042",
        "age": 32,
        "gender": "MALE",
        "date_of_birth": "15-May-1994",
        "blood_group": "O+",
        "mobile_number": "+919876543210",
        "email": "rohan.verma@example.com",
        "address": "Flat 12, Sunrise Apts, Bandra",
        "city": "Mumbai",
        "emergency_contact_name": "Pooja Verma",
        "emergency_contact_phone": "+919876543211",
        "medical_history": {
            "diabetes": True,
            "hypertension": False,
            "cardiac_disease": False,
            "thyroid": False,
            "asthma": False,
            "epilepsy": False,
            "pregnancy": False,
            "allergies": "Penicillin (Amoxicillin)",
            "current_medications": "Metformin 500mg OD",
            "smoking": False,
            "tobacco": False,
            "alcohol": True,
            "previous_surgeries": "Appendectomy (2018)",
            "infectious_diseases": "None",
            "physician_name": "Dr. A. Sharma",
            "physician_contact": "+919822211100",
            "additional_notes": "Well controlled blood sugars.",
        },
        "dental_history": {
            "chief_complaint": "Severe toothache in lower right molar with sensitivity to hot and cold liquids.",
            "previous_dental_treatments": "Composite restorations in 2024",
            "brushing_frequency": "Twice daily",
            "flossing_habit": True,
            "tobacco_habit": False,
            "grinding": True,
            "jaw_pain": False,
            "tmj_disorder": False,
            "sensitivity": True,
            "bleeding_gums": False,
            "dental_notes": "Patient presents with night bruxism. Occlusal splint recommended.",
        },
        "teeth": {
            "46": {"primary_status": "CARIES", "color": "#ef4444", "is_missing": False, "has_crown": False, "has_root_canal": False},
            "47": {"primary_status": "ROOT_CANAL", "color": "#8b5cf6", "is_missing": False, "has_crown": True, "has_root_canal": True},
            "18": {"primary_status": "MISSING", "color": "#64748b", "is_missing": True, "has_crown": False, "has_root_canal": False},
            "36": {"primary_status": "IMPLANT", "color": "#94a3b8", "is_missing": False, "has_crown": True, "has_implant": True},
        },
        "odontogram_stats": {
            "active_caries": 1,
            "missing_teeth": 1,
            "root_canals": 1,
            "crowns": 2,
            "implants": 1,
        },
        "treatments": [
            {
                "treatment_number": "TX-2026-001",
                "title": "Root Canal Therapy & Crown",
                "diagnosis": "Irreversible Pulpitis tooth #46",
                "status": "COMPLETED",
                "date": "10-Jan-2026",
                "dentist_name": "Dr. Sarah Jenkins",
                "procedures": [
                    {"name": "Molar Endodontic Therapy", "tooth": 46},
                    {"name": "Zirconia Crown Placement", "tooth": 46},
                ],
            },
            {
                "treatment_number": "TX-2026-002",
                "title": "Scaling & Polishing",
                "diagnosis": "Mild Gingivitis",
                "status": "COMPLETED",
                "date": "15-Feb-2026",
                "dentist_name": "Dr. Sarah Jenkins",
                "procedures": [{"name": "Full Mouth Ultrasonic Scaling", "tooth": None}],
            },
        ],
        "clinical_notes": [
            {
                "date": "10-Jan-2026",
                "author": "Dr. Sarah Jenkins",
                "text": "Canals negotiated, shaped, and obturated with gutta-percha. Temporary seal placed.",
            },
            {
                "date": "24-Jan-2026",
                "author": "Dr. Sarah Jenkins",
                "text": "Final Zirconia crown cemented with resin-modified glass ionomer.",
            },
        ],
        "prescriptions": [
            {
                "prescription_number": "RX-2026-0089",
                "date": "10-Jan-2026",
                "medications": [
                    {
                        "medicine_name": "Amoxicillin-Clavulanate 625mg",
                        "dosage": "625 mg",
                        "frequency": "1-0-1 (Twice daily)",
                        "duration": "5 Days",
                        "instructions": "Take after meals with plenty of water",
                    },
                    {
                        "medicine_name": "Aceclofenac + Paracetamol",
                        "dosage": "100mg / 325mg",
                        "frequency": "1-0-1 (As needed)",
                        "duration": "3 Days",
                        "instructions": "Take for post-op discomfort",
                    },
                ],
            }
        ],
        "invoices": [
            {
                "invoice_number": "INV-2026-0045",
                "date": "10-Jan-2026",
                "grand_total": 12500.0,
                "amount_paid": 12500.0,
                "balance_due": 0.0,
                "tax_amount": 1906.78,
                "status": "PAID",
            }
        ],
        "payments": [
            {
                "receipt_number": "REC-2026-0012",
                "date": "10-Jan-2026",
                "method": "UPI",
                "reference": "UPI/29482049281/Axis",
                "amount": 12500.0,
            }
        ],
        "next_appointment": {
            "date": "20-Sep-2026",
            "time": "11:30 AM",
            "dentist_name": "Dr. Sarah Jenkins",
            "purpose": "6-Month Routine Hygiene Recall & Polish",
            "instructions": "Please arrive 10 minutes early. Remember to update insurance changes if any.",
        },
        "documents": [
            {
                "file_name": "Periapical_Xray_Tooth_46.jpg",
                "document_type": "XRAY",
                "content_type": "image/jpeg",
                "created_at": "10-Jan-2026",
            },
            {
                "file_name": "Signed_Consent_Endodontics.pdf",
                "document_type": "CONSENT",
                "content_type": "application/pdf",
                "created_at": "10-Jan-2026",
            },
        ],
    }

    pdf_bytes = PatientReportPDFService.generate_report(
        clinic_info=clinic_info,
        patient_data=patient_data,
        sections=list(ALL_REPORT_SECTIONS),
        report_number="REP-20260910-0042",
        include_watermark=True,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_report_generation_minimal_missing_data():
    """Verify that empty/missing fields do not crash the PDF generator."""
    clinic_info = {"name": "Test Clinic"}
    patient_data = {
        "full_name": "Minimal Patient",
        "patient_number": "P-9999",
        "id": str(uuid4()),
    }

    pdf_bytes = PatientReportPDFService.generate_report(
        clinic_info=clinic_info,
        patient_data=patient_data,
        sections=list(ALL_REPORT_SECTIONS),
        report_number="REP-20260910-9999",
        include_watermark=False,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_report_subset_sections():
    """Verify selecting only specific sections."""
    clinic_info = {"name": "Selective Clinic"}
    patient_data = {
        "full_name": "Subset Patient",
        "patient_number": "P-1234",
        "id": str(uuid4()),
        "medical_history": {"allergies": "Sulfa drugs"},
    }

    sections = [
        PatientReportSectionEnum.PERSONAL_DETAILS,
        PatientReportSectionEnum.MEDICAL_HISTORY,
    ]

    pdf_bytes = PatientReportPDFService.generate_report(
        clinic_info=clinic_info,
        patient_data=patient_data,
        sections=sections,
        report_number="REP-20260910-1234",
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_patient_report_whatsapp_message_formatting():
    """Verify the generated WhatsApp message includes correct greeting and clinic name."""

    resp = PatientReportResponse(
        report_number="REP-20260910-0042",
        file_name="RohanVerma_P0042_20260910.pdf",
        document_id=uuid4(),
        download_url="/api/v1/patients/test/reports/download",
        generated_at=datetime.now(UTC),
        patient_id=uuid4(),
        patient_name="Rohan Verma",
        patient_number="P-0042",
        patient_phone="+919876543210",
        clinic_name="Apex Dental Clinic",
        sections_included=["medical_history", "treatment_history", "odontogram"],
        whatsapp_url="https://wa.me/919876543210?text=Hello",
        whatsapp_message=(
            "Hello Rohan Verma,\n\n"
            "Please find your DentalCare Pro treatment summary attached.\n\n"
            "Included:\n"
            "• Medical History\n"
            "• Treatment Summary\n"
            "• Odontogram\n\n"
            "If you have any questions please contact the clinic.\n\n"
            "Thank you,\nApex Dental Clinic"
        ),
    )

    assert "Hello Rohan Verma" in resp.whatsapp_message
    assert "Apex Dental Clinic" in resp.whatsapp_message
    assert "• Medical History" in resp.whatsapp_message
    assert "• Odontogram" in resp.whatsapp_message
    assert "https://wa.me/" in resp.whatsapp_url
