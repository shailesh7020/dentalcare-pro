import json
import logging
import re
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models import (
    AuditEvent,
    DentalHistory,
    MedicalHistory,
    Patient,
    PatientDocument,
    PatientTimelineEvent,
    User,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.billing import Invoice
from app.models.commercial import ClinicianSignature
from app.models.identity import Clinic
from app.models.odontogram import Tooth
from app.models.prescription import Prescription
from app.models.treatment import Treatment
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import DuplicateWarning, PatientInput, PatientUpdate
from app.schemas.patient_report import (
    PatientReportGenerateRequest,
    PatientReportResponse,
    PatientReportSectionEnum,
    PatientReportShareRequest,
)
from app.services.notifications.providers.email import EmailNotificationProvider
from app.services.notifications.providers.whatsapp import WhatsAppNotificationProvider
from app.services.patient_report_pdf_service import PatientReportPDFService


class PatientService:
    def __init__(self, db: AsyncSession, actor: User) -> None:
        if actor.clinic_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="A clinic context is required"
            )
        self.db = db
        self.actor = actor
        self.clinic_id = actor.clinic_id
        self.repository = PatientRepository(db)

    def _audit(self, action: str, patient: Patient) -> None:
        self.db.add(
            AuditEvent(
                clinic_id=self.clinic_id,
                actor_id=self.actor.id,
                action=action,
                entity_type="PATIENT",
                entity_id=str(patient.id),
            )
        )

    def _timeline(
        self, patient: Patient, event_type: str, title: str, description: str | None = None
    ) -> None:
        self.db.add(
            PatientTimelineEvent(
                patient_id=patient.id,
                clinic_id=self.clinic_id,
                event_type=event_type,
                title=title,
                description=description,
                actor_id=self.actor.id,
                created_by=self.actor.id,
                updated_by=self.actor.id,
            )
        )

    async def get(
        self, patient_id: UUID, include_deleted: bool = False, viewed: bool = False
    ) -> Patient:
        patient = await self.repository.get(self.clinic_id, patient_id, include_deleted)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        if viewed:
            self._audit("PATIENT_VIEWED", patient)
            await self.db.commit()
        return patient

    async def duplicates(
        self, payload: PatientInput | PatientUpdate, exclude_id: UUID | None = None
    ) -> list[DuplicateWarning]:
        patients = await self.repository.duplicates(
            self.clinic_id,
            payload.mobile_number,
            str(payload.email) if payload.email else None,
            payload.aadhaar_number,
            exclude_id,
        )
        warnings: list[DuplicateWarning] = []
        for patient in patients:
            if payload.mobile_number and patient.mobile_number == payload.mobile_number:
                warnings.append(
                    DuplicateWarning(
                        field="mobile_number",
                        patient_id=patient.id,
                        patient_number=patient.patient_number,
                    )
                )
            if (
                payload.email
                and patient.email
                and patient.email.lower() == str(payload.email).lower()
            ):
                warnings.append(
                    DuplicateWarning(
                        field="email", patient_id=patient.id, patient_number=patient.patient_number
                    )
                )
            if payload.aadhaar_number and patient.aadhaar_number == payload.aadhaar_number:
                warnings.append(
                    DuplicateWarning(
                        field="aadhaar_number",
                        patient_id=patient.id,
                        patient_number=patient.patient_number,
                    )
                )
        return warnings

    async def create(self, payload: PatientInput) -> tuple[Patient, list[DuplicateWarning]]:
        warnings = await self.duplicates(payload)
        data = payload.model_dump(exclude={"medical_history", "dental_history"}, exclude_none=True)
        patient = Patient(
            id=uuid4(),
            clinic_id=self.clinic_id,
            patient_number=f"P-{self.clinic_id.hex[:6].upper()}-{uuid4().hex[:8].upper()}",
            **data,
            created_by=self.actor.id,
            updated_by=self.actor.id,
        )
        self.db.add(patient)
        await self.db.flush()
        if payload.medical_history:
            self.db.add(
                MedicalHistory(
                    patient_id=patient.id,
                    **payload.medical_history.model_dump(),
                    created_by=self.actor.id,
                    updated_by=self.actor.id,
                )
            )
        if payload.dental_history:
            self.db.add(
                DentalHistory(
                    patient_id=patient.id,
                    **payload.dental_history.model_dump(),
                    created_by=self.actor.id,
                    updated_by=self.actor.id,
                )
            )
        self._audit("PATIENT_CREATED", patient)
        self._timeline(patient, "PATIENT_CREATED", "Patient registered")
        await self.db.commit()
        await self.db.refresh(patient)
        return patient, warnings

    async def update(
        self, patient_id: UUID, payload: PatientUpdate
    ) -> tuple[Patient, list[DuplicateWarning]]:
        patient = await self.get(patient_id)
        warnings = await self.duplicates(payload, patient.id)
        values = payload.model_dump(
            exclude_unset=True, exclude={"medical_history", "dental_history"}
        )
        for field, value in values.items():
            setattr(patient, field, value)
        patient.updated_by = self.actor.id
        if payload.medical_history is not None:
            history, _ = await self.repository.histories(patient.id)
            if history is None:
                self.db.add(
                    MedicalHistory(
                        patient_id=patient.id,
                        **payload.medical_history.model_dump(),
                        created_by=self.actor.id,
                        updated_by=self.actor.id,
                    )
                )
            else:
                for field, value in payload.medical_history.model_dump().items():
                    setattr(history, field, value)
                history.updated_by = self.actor.id
        if payload.dental_history is not None:
            _, history = await self.repository.histories(patient.id)
            if history is None:
                self.db.add(
                    DentalHistory(
                        patient_id=patient.id,
                        **payload.dental_history.model_dump(),
                        created_by=self.actor.id,
                        updated_by=self.actor.id,
                    )
                )
            else:
                for field, value in payload.dental_history.model_dump().items():
                    setattr(history, field, value)
                history.updated_by = self.actor.id
        self._audit("PATIENT_UPDATED", patient)
        self._timeline(patient, "PATIENT_UPDATED", "Patient record updated")
        await self.db.commit()
        await self.db.refresh(patient)
        return patient, warnings

    async def delete(self, patient_id: UUID) -> None:
        patient = await self.get(patient_id)
        patient.deleted_at = datetime.now(UTC)
        patient.updated_by = self.actor.id
        self._audit("PATIENT_DELETED", patient)
        self._timeline(patient, "PATIENT_DELETED", "Patient record archived")
        await self.db.commit()

    async def restore(self, patient_id: UUID) -> Patient:
        patient = await self.get(patient_id, include_deleted=True)
        if patient.deleted_at is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Patient is already active"
            )
        patient.deleted_at = None
        patient.updated_by = self.actor.id
        self._audit("PATIENT_RESTORED", patient)
        self._timeline(patient, "PATIENT_RESTORED", "Patient record restored")
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def list_documents(self, patient_id: UUID) -> list[PatientDocument]:
        await self.get(patient_id)
        return await self.repository.documents(self.clinic_id, patient_id)

    async def get_document(
        self, patient_id: UUID, document_id: UUID
    ) -> PatientDocument:
        await self.get(patient_id)
        doc = await self.repository.get_document(self.clinic_id, patient_id, document_id)
        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    async def upload_document(
        self,
        patient_id: UUID,
        file_name: str,
        content_type: str,
        storage_key: str,
        url: str,
        document_type: str = "DOCUMENT",
    ) -> PatientDocument:
        patient = await self.get(patient_id)
        document = PatientDocument(
            id=uuid4(),
            patient_id=patient.id,
            clinic_id=self.clinic_id,
            file_name=file_name,
            content_type=content_type,
            storage_key=storage_key,
            document_type=document_type,
            created_by=self.actor.id,
            updated_by=self.actor.id,
        )
        self.db.add(document)
        if document_type == "PHOTO":
            patient.photo_url = url
        self._audit("PATIENT_DOCUMENT_UPLOADED", patient)
        self._timeline(
            patient, "PATIENT_DOCUMENT_UPLOADED", "Patient document uploaded", document.file_name
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def generate_patient_report(
        self,
        patient_id: UUID,
        payload: PatientReportGenerateRequest,
        storage_service: Any = None,
    ) -> tuple[bytes, PatientReportResponse]:
        # 1. Fetch Patient with medical and dental history
        stmt_patient = (
            select(Patient)
            .options(
                selectinload(Patient.medical_history),
                selectinload(Patient.dental_history),
            )
            .where(
                Patient.id == patient_id,
                Patient.clinic_id == self.clinic_id,
                Patient.deleted_at.is_(None),
            )
        )
        patient_row = await self.db.execute(stmt_patient)
        patient = patient_row.scalar_one_or_none()
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
            )

        clinic = await self.db.get(Clinic, self.clinic_id)
        clinic_info = {
            "id": str(self.clinic_id),
            "name": (clinic.name if clinic and clinic.name else "DentalCare Pro Clinic"),
            "phone": (clinic.phone if clinic and clinic.phone else "+91 99000 11223"),
            "email": (clinic.email if clinic and clinic.email else "contact@dentalcarepro.in"),
            "address": (clinic.address if clinic and clinic.address else "101 Medical Center, Dental Tower"),
        }

        # 3. Clinician Signature
        stmt_sig = select(ClinicianSignature).where(
            ClinicianSignature.user_id == self.actor.id,
            ClinicianSignature.is_active.is_(True),
            ClinicianSignature.deleted_at.is_(None),
        )
        sig_row = await self.db.execute(stmt_sig)
        clinician_sig = sig_row.scalar_one_or_none()
        sig_data = clinician_sig.signature_data if clinician_sig else None

        # 4. Assembled Patient Record
        patient_data: dict[str, Any] = {
            "id": str(patient.id),
            "full_name": f"{patient.first_name} {patient.last_name}",
            "patient_number": patient.patient_number,
            "age": patient.age,
            "gender": str(patient.gender),
            "date_of_birth": (
                patient.date_of_birth.strftime("%d-%b-%Y")
                if patient.date_of_birth
                else "—"
            ),
            "blood_group": patient.blood_group or "—",
            "mobile_number": patient.mobile_number,
            "email": patient.email,
            "address": patient.address,
            "city": patient.city,
            "emergency_contact_name": patient.emergency_contact_name,
            "emergency_contact_phone": patient.emergency_contact_number,
            "medical_history": {
                "diabetes": (
                    patient.medical_history.diabetes
                    if patient.medical_history
                    else False
                ),
                "hypertension": (
                    patient.medical_history.hypertension
                    if patient.medical_history
                    else False
                ),
                "cardiac_disease": (
                    patient.medical_history.cardiac_disease
                    if patient.medical_history
                    else False
                ),
                "thyroid": (
                    patient.medical_history.thyroid
                    if patient.medical_history
                    else False
                ),
                "asthma": (
                    patient.medical_history.asthma
                    if patient.medical_history
                    else False
                ),
                "epilepsy": (
                    patient.medical_history.epilepsy
                    if patient.medical_history
                    else False
                ),
                "pregnancy": (
                    patient.medical_history.pregnancy
                    if patient.medical_history
                    else False
                ),
                "allergies": (
                    patient.medical_history.allergies
                    if patient.medical_history
                    else None
                ),
                "current_medications": (
                    patient.medical_history.current_medications
                    if patient.medical_history
                    else None
                ),
                "smoking": (
                    patient.medical_history.smoking
                    if patient.medical_history
                    else False
                ),
                "tobacco": (
                    patient.medical_history.tobacco
                    if patient.medical_history
                    else False
                ),
                "alcohol": (
                    patient.medical_history.alcohol
                    if patient.medical_history
                    else False
                ),
                "previous_surgeries": (
                    patient.medical_history.previous_surgeries
                    if patient.medical_history
                    else None
                ),
                "infectious_diseases": (
                    patient.medical_history.infectious_diseases
                    if patient.medical_history
                    else None
                ),
                "physician_name": (
                    patient.medical_history.physician_name
                    if patient.medical_history
                    else None
                ),
                "physician_contact": (
                    patient.medical_history.physician_contact
                    if patient.medical_history
                    else None
                ),
                "additional_notes": (
                    patient.medical_history.additional_notes
                    if patient.medical_history
                    else None
                ),
            },
            "dental_history": {
                "chief_complaint": (
                    patient.dental_history.chief_complaint
                    if patient.dental_history
                    else None
                ),
                "previous_dental_treatments": (
                    patient.dental_history.previous_dental_treatments
                    if patient.dental_history
                    else None
                ),
                "brushing_frequency": (
                    patient.dental_history.brushing_frequency
                    if patient.dental_history
                    else None
                ),
                "flossing_habit": (
                    patient.dental_history.flossing_habit
                    if patient.dental_history
                    else False
                ),
                "tobacco_habit": (
                    patient.dental_history.tobacco_habit
                    if patient.dental_history
                    else False
                ),
                "grinding": (
                    patient.dental_history.grinding
                    if patient.dental_history
                    else False
                ),
                "jaw_pain": (
                    patient.dental_history.jaw_pain
                    if patient.dental_history
                    else False
                ),
                "tmj_disorder": (
                    patient.dental_history.tmj_disorder
                    if patient.dental_history
                    else False
                ),
                "sensitivity": (
                    patient.dental_history.sensitivity
                    if patient.dental_history
                    else False
                ),
                "bleeding_gums": (
                    patient.dental_history.bleeding_gums
                    if patient.dental_history
                    else False
                ),
                "dental_notes": (
                    patient.dental_history.dental_notes
                    if patient.dental_history
                    else None
                ),
            },
        }

        # 5. Treatments
        stmt_tx = (
            select(Treatment)
            .options(
                selectinload(Treatment.procedures),
                selectinload(Treatment.dentist),
            )
            .where(
                Treatment.patient_id == patient_id,
                Treatment.clinic_id == self.clinic_id,
                Treatment.deleted_at.is_(None),
            )
            .order_by(Treatment.created_at.desc())
        )
        tx_rows = await self.db.execute(stmt_tx)
        treatments = list(tx_rows.scalars().all())
        patient_data["treatments"] = [
            {
                "treatment_number": tx.treatment_number,
                "title": tx.procedure_performed or tx.diagnosis or "Clinical Procedure",
                "diagnosis": tx.diagnosis,
                "status": str(tx.status),
                "date": (
                    tx.created_at.strftime("%d-%b-%Y")
                    if tx.created_at
                    else "—"
                ),
                "dentist_name": (
                    f"Dr. {tx.dentist.first_name} {tx.dentist.last_name}"
                    if tx.dentist
                    else "Attending Dentist"
                ),
                "procedures": [
                    {"name": p.procedure_name, "tooth": p.tooth_number}
                    for p in tx.procedures
                ],
            }
            for tx in treatments
        ]
        patient_data["clinical_notes"] = [
            {
                "date": tx.created_at.strftime("%d-%b-%Y"),
                "author": (
                    f"Dr. {tx.dentist.first_name} {tx.dentist.last_name}"
                    if tx.dentist
                    else "Clinician"
                ),
                "text": tx.clinical_notes,
            }
            for tx in treatments
            if tx.clinical_notes
        ]

        # 6. Odontogram / Teeth
        stmt_teeth = (
            select(Tooth)
            .options(selectinload(Tooth.surfaces))
            .where(
                Tooth.patient_id == patient_id,
                Tooth.clinic_id == self.clinic_id,
                Tooth.deleted_at.is_(None),
            )
        )
        teeth_rows = await self.db.execute(stmt_teeth)
        teeth = list(teeth_rows.scalars().all())
        teeth_dict: dict[str, Any] = {}
        active_caries = 0
        missing_count = 0
        rct_count = 0
        crown_count = 0
        implant_count = 0
        for t in teeth:
            teeth_dict[str(t.tooth_number)] = {
                "primary_status": t.primary_status,
                "color": t.color,
                "is_missing": t.is_missing,
                "has_crown": t.has_crown,
                "has_root_canal": t.has_root_canal,
                "has_implant": t.has_implant,
            }
            if t.is_missing:
                missing_count += 1
            if t.has_crown:
                crown_count += 1
            if t.has_root_canal:
                rct_count += 1
            if t.has_implant:
                implant_count += 1
            if t.primary_status == "CARIES":
                active_caries += 1

        patient_data["teeth"] = teeth_dict
        patient_data["odontogram_stats"] = {
            "active_caries": active_caries,
            "missing_teeth": missing_count,
            "root_canals": rct_count,
            "crowns": crown_count,
            "implants": implant_count,
        }

        # 7. Prescriptions
        stmt_rx = (
            select(Prescription)
            .options(
                selectinload(Prescription.items),
                selectinload(Prescription.dentist),
            )
            .where(
                Prescription.patient_id == patient_id,
                Prescription.clinic_id == self.clinic_id,
                Prescription.deleted_at.is_(None),
            )
            .order_by(Prescription.date.desc())
        )
        rx_rows = await self.db.execute(stmt_rx)
        prescriptions = list(rx_rows.scalars().all())
        patient_data["prescriptions"] = [
            {
                "prescription_number": rx.prescription_number,
                "date": rx.date.strftime("%d-%b-%Y") if rx.date else "—",
                "medications": [
                    {
                        "medicine_name": m.medicine_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "duration": m.duration,
                        "instructions": m.food_instructions or m.notes or "As prescribed",
                    }
                    for m in rx.items
                ],
            }
            for rx in prescriptions
        ]

        # 8. Invoices & Payments
        stmt_inv = (
            select(Invoice)
            .options(
                selectinload(Invoice.payments),
                selectinload(Invoice.items),
            )
            .where(
                Invoice.patient_id == patient_id,
                Invoice.clinic_id == self.clinic_id,
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.date.desc())
        )
        inv_rows = await self.db.execute(stmt_inv)
        invoices = list(inv_rows.scalars().all())
        patient_data["invoices"] = [
            {
                "invoice_number": inv.invoice_number,
                "date": inv.date.strftime("%d-%b-%Y") if inv.date else "—",
                "grand_total": inv.grand_total,
                "amount_paid": inv.amount_paid,
                "balance_due": inv.balance_due,
                "tax_amount": inv.tax_amount,
                "status": str(inv.status),
            }
            for inv in invoices
        ]
        all_payments = []
        for inv in invoices:
            for p in inv.payments:
                if p.deleted_at is None:
                    all_payments.append(
                        {
                            "receipt_number": p.receipt_number,
                            "date": (
                                p.payment_date.strftime("%d-%b-%Y")
                                if p.payment_date
                                else "—"
                            ),
                            "method": str(p.method),
                            "reference": p.transaction_reference or "—",
                            "amount": p.amount,
                        }
                    )
        patient_data["payments"] = all_payments

        # 9. Next Appointment
        stmt_appt = (
            select(Appointment)
            .options(selectinload(Appointment.dentist))
            .where(
                Appointment.patient_id == patient_id,
                Appointment.clinic_id == self.clinic_id,
                Appointment.status.in_(
                    [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
                ),
                Appointment.date >= datetime.now(UTC).date(),
                Appointment.deleted_at.is_(None),
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
            .limit(1)
        )
        next_appt = (await self.db.execute(stmt_appt)).scalar_one_or_none()
        if next_appt:
            patient_data["next_appointment"] = {
                "date": next_appt.date.strftime("%d-%b-%Y"),
                "time": next_appt.start_time.strftime("%I:%M %p"),
                "dentist_name": (
                    f"Dr. {next_appt.dentist.first_name} {next_appt.dentist.last_name}"
                    if next_appt.dentist
                    else "Attending Dentist"
                ),
                "purpose": (
                    next_appt.visit_type.value
                    if hasattr(next_appt.visit_type, "value")
                    else str(next_appt.visit_type)
                ) or "Dental Examination",
                "instructions": (
                    next_appt.notes
                    or "Please arrive 10 minutes prior to scheduled time."
                ),
            }
        else:
            patient_data["next_appointment"] = None

        # 10. Documents
        stmt_doc = (
            select(PatientDocument)
            .where(
                PatientDocument.patient_id == patient_id,
                PatientDocument.clinic_id == self.clinic_id,
                PatientDocument.deleted_at.is_(None),
            )
            .order_by(PatientDocument.created_at.desc())
        )
        docs = list((await self.db.execute(stmt_doc)).scalars().all())
        patient_data["documents"] = [
            {
                "file_name": d.file_name,
                "document_type": d.document_type,
                "content_type": d.content_type,
                "created_at": d.created_at.strftime("%d-%b-%Y"),
            }
            for d in docs
        ]

        # 11. Format File Name & Report Number
        clean_first = re.sub(r"[^a-zA-Z0-9]", "", str(patient.first_name or "Patient")).upper()
        clean_last = re.sub(r"[^a-zA-Z0-9]", "", str(patient.last_name or "")).upper()
        patient_slug = f"{clean_first}_{clean_last}".strip("_") if clean_last else clean_first
        clean_id = re.sub(r"[^a-zA-Z0-9]", "", str(patient.patient_number))
        timestamp_day = datetime.now(UTC).strftime("%Y%m%d")
        file_name = f"{patient_slug}_Dental_Report.pdf"
        report_number = f"REP-{timestamp_day}-{clean_id[-4:] if len(clean_id) >= 4 else '0001'}"

        # 12. Generate PDF Bytes
        pdf_bytes = PatientReportPDFService.generate_report(
            clinic_info=clinic_info,
            patient_data=patient_data,
            sections=payload.sections,
            report_number=report_number,
            include_watermark=payload.include_watermark,
            dentist_signature_data=sig_data,
        )

        # 13. Save to patient documents if requested
        doc_id: UUID | None = None
        if payload.save_to_documents and storage_service:
            key, _url = await storage_service.save_patient_bytes(
                clinic_id=self.clinic_id,
                patient_id=patient.id,
                content=pdf_bytes,
                filename=file_name,
            )
            saved_doc = PatientDocument(
                id=uuid4(),
                patient_id=patient.id,
                clinic_id=self.clinic_id,
                file_name=file_name,
                content_type="application/pdf",
                storage_key=key,
                document_type="REPORT",
                created_by=self.actor.id,
                updated_by=self.actor.id,
            )
            self.db.add(saved_doc)
            doc_id = saved_doc.id

        # 14. Audit Log
        self.db.add(
            AuditEvent(
                clinic_id=self.clinic_id,
                actor_id=self.actor.id,
                action="PATIENT_REPORT_GENERATED",
                entity_type="PATIENT_REPORT",
                entity_id=str(patient.id),
                metadata_json=json.dumps(
                    {
                        "report_number": report_number,
                        "file_name": file_name,
                        "sections": [str(s) for s in payload.sections],
                        "save_to_documents": payload.save_to_documents,
                        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
                        "time": datetime.now(UTC).strftime("%H:%M:%S UTC"),
                        "delivery_method": "DOWNLOAD/PREVIEW",
                    }
                ),
            )
        )
        self._timeline(
            patient,
            "PATIENT_REPORT_GENERATED",
            f"Patient Report #{report_number} generated",
            f"Sections included: {len(payload.sections)}. File: {file_name}",
        )
        await self.db.commit()

        # 15. Format WhatsApp Message & Secure Download Token
        settings = get_settings()
        share_token = jwt.encode(
            {
                "sub": str(self.actor.id),
                "patient_id": str(patient.id),
                "exp": datetime.now(UTC) + timedelta(days=7),
            },
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )
        download_path = (
            f"/api/v1/patients/{patient.id}/reports/download"
            f"?report_number={report_number}&token={share_token}"
        )

        section_titles = {
            PatientReportSectionEnum.MEDICAL_HISTORY: "Medical History",
            PatientReportSectionEnum.TREATMENT_HISTORY: "Treatment Summary",
            PatientReportSectionEnum.ODONTOGRAM: "Odontogram",
            PatientReportSectionEnum.PRESCRIPTIONS: "Prescription",
            PatientReportSectionEnum.RECEIPTS: "Payment Receipt",
            PatientReportSectionEnum.INVOICES: "Invoice Summary",
            PatientReportSectionEnum.NEXT_APPOINTMENT: "Next Appointment",
            PatientReportSectionEnum.CLINICAL_NOTES: "Clinical Notes",
        }
        included_bullets = [
            f"• {section_titles[s]}"
            for s in payload.sections
            if s in section_titles
        ]
        bullet_text = (
            "\n".join(included_bullets)
            if included_bullets
            else "• Complete Dental Records"
        )

        raw_msg = (
            f"Hello {patient.first_name} {patient.last_name},\n\n"
            f"Please find your DentalCare Pro treatment summary attached.\n\n"
            f"Included:\n{bullet_text}\n\n"
            f"If you have any questions please contact the clinic.\n\n"
            f"Thank you,\n{clinic_info['name']}"
        )
        encoded_msg = urllib.parse.quote(raw_msg)
        phone = (
            (patient.mobile_number or "")
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
        )
        wa_url = (
            f"https://wa.me/{phone}?text={encoded_msg}"
            if phone
            else f"https://wa.me/?text={encoded_msg}"
        )

        resp = PatientReportResponse(
            report_number=report_number,
            file_name=file_name,
            document_id=doc_id,
            download_url=download_path,
            generated_at=datetime.now(UTC),
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            patient_number=patient.patient_number,
            patient_phone=patient.mobile_number,
            patient_email=patient.email,
            clinic_name=clinic_info["name"],
            sections_included=[str(s) for s in payload.sections],
            whatsapp_url=wa_url,
            whatsapp_message=raw_msg,
        )
        return pdf_bytes, resp

    async def share_patient_report(
        self, patient_id: UUID, payload: PatientReportShareRequest
    ) -> dict[str, Any]:
        patient = await self.get(patient_id)
        clinic = await self.db.get(Clinic, self.clinic_id)
        clinic_name = (clinic.name if clinic and clinic.name else "DentalCare Pro Clinic")

        clean_first = re.sub(r"[^a-zA-Z0-9]", "", str(patient.first_name or "Patient")).upper()
        clean_last = re.sub(r"[^a-zA-Z0-9]", "", str(patient.last_name or "")).upper()
        patient_slug = f"{clean_first}_{clean_last}".strip("_") if clean_last else clean_first
        file_name = f"{patient_slug}_Dental_Report.pdf"

        # Direct WhatsApp PDF Document Dispatch
        if payload.delivery_method.upper() == "WHATSAPP":
            pdf_bytes: bytes | None = None
            if payload.report_id:
                try:
                    doc = await self.get_document(patient_id, payload.report_id)
                    file_path = get_settings().storage_local_path / doc.storage_key
                    if file_path.exists() and file_path.is_file():
                        pdf_bytes = file_path.read_bytes()
                        file_name = doc.file_name or file_name
                except (OSError, ValueError, HTTPException) as exc:
                    logging.getLogger(__name__).warning(
                        "Unable to read stored report %s for patient %s: %s",
                        payload.report_id,
                        patient_id,
                        exc,
                    )
                    pdf_bytes = None

            if not pdf_bytes:
                pdf_bytes, meta = await self.generate_patient_report(
                    patient_id=patient_id,
                    payload=PatientReportGenerateRequest(save_to_documents=False),
                    storage_service=None,
                )
                file_name = meta.file_name

            caption = (
                f"Hello {patient.first_name} {patient.last_name},\n\n"
                f"Please find your DentalCare Pro treatment summary attached.\n\n"
                f"Included:\n"
                f"• Medical History\n"
                f"• Treatment Summary\n"
                f"• Odontogram\n"
                f"• Clinical Notes\n"
                f"• Prescription\n"
                f"• Payment Receipt\n"
                f"• Invoice Summary\n"
                f"• Next Appointment\n\n"
                f"If you have any questions please contact the clinic.\n\n"
                f"Thank you,\n{clinic_name}"
            )

            wa_res = await WhatsAppNotificationProvider.send_document(
                recipient=payload.recipient,
                filename=file_name,
                caption=caption,
                pdf_bytes=pdf_bytes,
            )
            if not wa_res.get("success"):
                return wa_res

        # Record Audit
        self.db.add(
            AuditEvent(
                clinic_id=self.clinic_id,
                actor_id=self.actor.id,
                action="PATIENT_REPORT_SHARED",
                entity_type="PATIENT_REPORT",
                entity_id=str(patient.id),
                metadata_json=json.dumps(
                    {
                        "recipient": payload.recipient,
                        "delivery_method": payload.delivery_method,
                        "report_id": (
                            str(payload.report_id) if payload.report_id else None
                        ),
                        "notes": payload.notes,
                        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
                        "time": datetime.now(UTC).strftime("%H:%M:%S UTC"),
                    }
                ),
            )
        )
        self._timeline(
            patient,
            "PATIENT_REPORT_SHARED",
            f"Patient report shared via {payload.delivery_method}",
            f"Recipient: {payload.recipient} | File: {file_name}",
        )
        await self.db.commit()

        # Email dispatch
        if payload.delivery_method.upper() == "EMAIL":
            provider = EmailNotificationProvider()
            await provider.send(
                recipient=payload.recipient,
                title="Your Dental Treatment Report",
                message=(
                    f"Dear {patient.first_name} {patient.last_name},\n\n"
                    f"Please find your dental treatment report ({file_name}) attached.\n\n"
                    f"Best regards,\n{clinic_name}"
                ),
            )

        return {
            "success": True,
            "delivery_method": payload.delivery_method,
            "recipient": payload.recipient,
            "filename": file_name,
            "message": f"Directly sent PDF '{file_name}' to {payload.recipient} via {payload.delivery_method}!",
        }


