from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent_form import (
    FormStatus,
    FormType,
    PatientForm,
)
from app.models.patient import Patient
from app.repositories.consent_form_repository import ConsentFormRepository
from app.schemas.consent_form import (
    ConsentRecordCreate,
    ConsentRecordRead,
    FormTemplateCreate,
    FormTemplateRead,
    FormTemplateUpdate,
    PatientFormCreate,
    PatientFormRead,
    PatientFormReview,
    PatientFormSubmit,
)


class ConsentFormService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ConsentFormRepository(db)

    # ----------------------------------------------------
    # Form Templates
    # ----------------------------------------------------
    async def create_template(
        self, clinic_id: UUID, payload: FormTemplateCreate
    ) -> FormTemplateRead:
        item = await self.repo.create_template(clinic_id, payload)
        await self.db.commit()
        return FormTemplateRead.model_validate(item)

    async def list_templates(
        self, clinic_id: UUID, form_type: FormType | None = None
    ) -> list[FormTemplateRead]:
        items = await self.repo.list_templates(clinic_id, form_type)
        return [FormTemplateRead.model_validate(i) for i in items]

    async def get_template(self, clinic_id: UUID, template_id: UUID) -> FormTemplateRead:
        tmpl = await self.repo.get_template(clinic_id, template_id)
        if not tmpl:
            raise HTTPException(status_code=404, detail="Form template not found.")
        return FormTemplateRead.model_validate(tmpl)

    async def update_template(
        self, clinic_id: UUID, template_id: UUID, payload: FormTemplateUpdate
    ) -> FormTemplateRead:
        tmpl = await self.repo.get_template(clinic_id, template_id)
        if not tmpl:
            raise HTTPException(status_code=404, detail="Form template not found.")
        for field, val in payload.model_dump(exclude_unset=True).items():
            setattr(tmpl, field, val)
        await self.db.commit()
        return FormTemplateRead.model_validate(tmpl)

    async def seed_clinical_templates(self, clinic_id: UUID) -> None:
        existing = await self.repo.list_templates(clinic_id)
        if existing:
            return

        defaults = [
            FormTemplateCreate(
                title="Adult Medical & Dental History Questionnaire",
                description="Comprehensive systemic health screening, allergies, and current medications.",
                form_type=FormType.MEDICAL_HISTORY,
                schema_json=json.dumps([
                    {"id": "q1", "type": "boolean", "label": "Are you currently taking any prescription medications?", "required": True},
                    {"id": "q2", "type": "text", "label": "List any known drug or latex allergies:", "required": False},
                    {"id": "q3", "type": "boolean", "label": "Do you have a history of high blood pressure or cardiac conditions?", "required": True},
                    {"id": "q4", "type": "boolean", "label": "Do you have diabetes or bleeding disorders?", "required": True},
                ]),
            ),
            FormTemplateCreate(
                title="Informed Consent for Root Canal Treatment",
                description="Surgical and endodontic procedure consent, potential risks, and prognosis.",
                form_type=FormType.TREATMENT_CONSENT,
                schema_json=json.dumps([
                    {"id": "q1", "type": "checkbox", "label": "I understand root canal therapy involves cleaning and sealing root canals.", "required": True},
                    {"id": "q2", "type": "checkbox", "label": "I acknowledge post-operative sensitivity may occur for several days.", "required": True},
                    {"id": "q3", "type": "checkbox", "label": "I understand a permanent crown restoration is recommended following treatment.", "required": True},
                ]),
            ),
            FormTemplateCreate(
                title="Informed Consent for Surgical Dental Extraction",
                description="Extraction of erupted/impacted teeth, local anesthesia, and dry socket risk awareness.",
                form_type=FormType.SURGICAL_CONSENT,
                schema_json=json.dumps([
                    {"id": "q1", "type": "checkbox", "label": "I authorize the dentist to perform dental extraction under local anesthesia.", "required": True},
                    {"id": "q2", "type": "checkbox", "label": "I understand common risks including bleeding, swelling, bruising, and dry socket.", "required": True},
                ]),
            ),
        ]

        for d in defaults:
            await self.repo.create_template(clinic_id, d)
        await self.db.commit()

    # ----------------------------------------------------
    # Patient Forms
    # ----------------------------------------------------
    async def assign_patient_form(
        self, clinic_id: UUID, payload: PatientFormCreate
    ) -> PatientFormRead:
        tmpl = await self.repo.get_template(clinic_id, payload.template_id)
        if not tmpl:
            raise HTTPException(status_code=404, detail="Form template not found.")

        form = PatientForm(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            template_id=payload.template_id,
            status=FormStatus.PENDING,
            answers_json=payload.answers_json,
        )
        self.db.add(form)
        await self.db.commit()
        await self.db.refresh(form)

        patient = await self.db.get(Patient, payload.patient_id)
        return PatientFormRead(
            id=form.id,
            clinic_id=form.clinic_id,
            patient_id=form.patient_id,
            patient_name=f"{patient.first_name} {patient.last_name}" if patient else None,
            template_id=form.template_id,
            template_title=tmpl.title,
            status=form.status,
            answers_json=form.answers_json,
            submitted_at=form.submitted_at,
            created_at=form.created_at,
        )

    async def get_patient_form(self, clinic_id: UUID, form_id: UUID) -> PatientFormRead:
        form = await self.repo.get_patient_form(clinic_id, form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Patient form not found.")
        return PatientFormRead(
            id=form.id,
            clinic_id=form.clinic_id,
            patient_id=form.patient_id,
            patient_name=f"{form.patient.first_name} {form.patient.last_name}" if form.patient else None,
            template_id=form.template_id,
            template_title=form.template.title if form.template else None,
            status=form.status,
            answers_json=form.answers_json,
            submitted_at=form.submitted_at,
            reviewed_at=form.reviewed_at,
            reviewed_by_id=form.reviewed_by_id,
            reviewed_by_name=f"{form.reviewed_by.first_name} {form.reviewed_by.last_name}" if form.reviewed_by else None,
            notes=form.notes,
            created_at=form.created_at,
        )

    async def submit_patient_form(
        self, clinic_id: UUID, form_id: UUID, payload: PatientFormSubmit
    ) -> PatientFormRead:
        form = await self.repo.get_patient_form(clinic_id, form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Patient form not found.")

        form.answers_json = payload.answers_json
        form.status = FormStatus.SUBMITTED
        form.submitted_at = datetime.now(UTC)
        await self.db.commit()

        return PatientFormRead(
            id=form.id,
            clinic_id=form.clinic_id,
            patient_id=form.patient_id,
            patient_name=f"{form.patient.first_name} {form.patient.last_name}" if form.patient else None,
            template_id=form.template_id,
            template_title=form.template.title if form.template else None,
            status=form.status,
            answers_json=form.answers_json,
            submitted_at=form.submitted_at,
            reviewed_at=form.reviewed_at,
            reviewed_by_id=form.reviewed_by_id,
            notes=form.notes,
            created_at=form.created_at,
        )

    async def list_patient_forms(
        self, clinic_id: UUID, patient_id: UUID | None = None, status: FormStatus | None = None
    ) -> list[PatientFormRead]:
        forms = await self.repo.list_patient_forms(clinic_id, patient_id=patient_id, status=status)
        return [
            PatientFormRead(
                id=f.id,
                clinic_id=f.clinic_id,
                patient_id=f.patient_id,
                patient_name=f"{f.patient.first_name} {f.patient.last_name}" if f.patient else None,
                template_id=f.template_id,
                template_title=f.template.title if f.template else None,
                status=f.status,
                answers_json=f.answers_json,
                submitted_at=f.submitted_at,
                reviewed_at=f.reviewed_at,
                reviewed_by_id=f.reviewed_by_id,
                reviewed_by_name=f"{f.reviewed_by.first_name} {f.reviewed_by.last_name}" if f.reviewed_by else None,
                notes=f.notes,
                created_at=f.created_at,
            )
            for f in forms
        ]

    async def review_patient_form(
        self, clinic_id: UUID, form_id: UUID, reviewer_id: UUID, payload: PatientFormReview
    ) -> PatientFormRead:
        form = await self.repo.get_patient_form(clinic_id, form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Patient form not found.")

        updated = await self.repo.review_patient_form(form, payload, reviewer_id=reviewer_id)
        await self.db.commit()

        return PatientFormRead(
            id=updated.id,
            clinic_id=updated.clinic_id,
            patient_id=updated.patient_id,
            patient_name=f"{updated.patient.first_name} {updated.patient.last_name}" if updated.patient else None,
            template_id=updated.template_id,
            template_title=updated.template.title if updated.template else None,
            status=updated.status,
            answers_json=updated.answers_json,
            submitted_at=updated.submitted_at,
            reviewed_at=updated.reviewed_at,
            reviewed_by_id=updated.reviewed_by_id,
            notes=updated.notes,
            created_at=updated.created_at,
        )

    # ----------------------------------------------------
    # Consent Records
    # ----------------------------------------------------
    async def record_consent(
        self, clinic_id: UUID, payload: ConsentRecordCreate, ip_address: str | None = None
    ) -> ConsentRecordRead:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        record = await self.repo.create_consent_record(clinic_id, payload, ip_address=ip_address)
        await self.db.commit()

        return ConsentRecordRead(
            id=record.id,
            clinic_id=record.clinic_id,
            patient_id=record.patient_id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            treatment_id=record.treatment_id,
            consent_type=record.consent_type,
            title=record.title,
            content_text=record.content_text,
            patient_signature=record.patient_signature,
            signed_at=record.signed_at,
            ip_address=record.ip_address,
            witness_name=record.witness_name,
            version=record.version,
            expires_at=record.expires_at,
            created_at=record.created_at,
        )

    async def get_consent_record(
        self, clinic_id: UUID, consent_id: UUID
    ) -> ConsentRecordRead:
        rec = await self.repo.get_consent_record(clinic_id, consent_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Consent record not found.")
        return ConsentRecordRead.model_validate(rec)

    async def list_consent_records(
        self, clinic_id: UUID, patient_id: UUID | None = None, treatment_id: UUID | None = None
    ) -> list[ConsentRecordRead]:
        items = await self.repo.list_consent_records(clinic_id, patient_id)
        if treatment_id:
            items = [i for i in items if i.treatment_id == treatment_id]
        return [
            ConsentRecordRead(
                id=c.id,
                clinic_id=c.clinic_id,
                patient_id=c.patient_id,
                patient_name=f"{c.patient.first_name} {c.patient.last_name}" if c.patient else None,
                treatment_id=c.treatment_id,
                consent_type=c.consent_type,
                title=c.title,
                content_text=c.content_text,
                patient_signature=c.patient_signature,
                signed_at=c.signed_at,
                ip_address=c.ip_address,
                witness_name=c.witness_name,
                version=c.version,
                expires_at=c.expires_at,
                created_at=c.created_at,
            )
            for c in items
        ]
