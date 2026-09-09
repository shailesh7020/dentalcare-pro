from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.consent_form import (
    ConsentRecord,
    FormStatus,
    FormTemplate,
    FormType,
    PatientForm,
)
from app.schemas.consent_form import (
    ConsentRecordCreate,
    FormTemplateCreate,
    PatientFormCreate,
    PatientFormReview,
)


class ConsentFormRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------
    # Form Templates
    # ----------------------------------------------------
    async def create_template(
        self, clinic_id: UUID, payload: FormTemplateCreate, actor_id: UUID | None = None
    ) -> FormTemplate:
        template = FormTemplate(
            id=uuid4(),
            clinic_id=clinic_id,
            title=payload.title,
            description=payload.description,
            form_type=payload.form_type,
            version=1,
            schema_json=payload.schema_json,
            is_active=payload.is_active,
            created_by=actor_id,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def get_template(self, clinic_id: UUID, template_id: UUID) -> FormTemplate | None:
        stmt = select(FormTemplate).where(
            FormTemplate.id == template_id,
            (FormTemplate.clinic_id == clinic_id) | (FormTemplate.clinic_id.is_(None)),
            FormTemplate.deleted_at.is_(None),
        )
        return await self.db.scalar(stmt)

    async def list_templates(
        self, clinic_id: UUID, form_type: FormType | None = None
    ) -> list[FormTemplate]:
        stmt = select(FormTemplate).where(
            (FormTemplate.clinic_id == clinic_id) | (FormTemplate.clinic_id.is_(None)),
            FormTemplate.deleted_at.is_(None),
        )
        if form_type:
            stmt = stmt.where(FormTemplate.form_type == form_type)
        stmt = stmt.order_by(FormTemplate.title)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ----------------------------------------------------
    # Patient Forms
    # ----------------------------------------------------
    async def create_patient_form(
        self, clinic_id: UUID, patient_id: UUID, payload: PatientFormCreate
    ) -> PatientForm:
        form = PatientForm(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            template_id=payload.template_id,
            status=FormStatus.SUBMITTED,
            answers_json=payload.answers_json,
            submitted_at=datetime.now(UTC),
        )
        self.db.add(form)
        await self.db.flush()
        return form

    async def get_patient_form(self, clinic_id: UUID, form_id: UUID) -> PatientForm | None:
        stmt = (
            select(PatientForm)
            .options(
                selectinload(PatientForm.patient),
                selectinload(PatientForm.template),
                selectinload(PatientForm.reviewed_by),
            )
            .where(
                PatientForm.id == form_id,
                PatientForm.clinic_id == clinic_id,
                PatientForm.deleted_at.is_(None),
            )
        )
        return await self.db.scalar(stmt)

    async def list_patient_forms(
        self, clinic_id: UUID, patient_id: UUID | None = None, status: FormStatus | None = None
    ) -> list[PatientForm]:
        stmt = (
            select(PatientForm)
            .options(
                selectinload(PatientForm.patient),
                selectinload(PatientForm.template),
                selectinload(PatientForm.reviewed_by),
            )
            .where(
                PatientForm.clinic_id == clinic_id,
                PatientForm.deleted_at.is_(None),
            )
        )
        if patient_id:
            stmt = stmt.where(PatientForm.patient_id == patient_id)
        if status:
            stmt = stmt.where(PatientForm.status == status)

        stmt = stmt.order_by(PatientForm.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def review_patient_form(
        self, form: PatientForm, payload: PatientFormReview, reviewer_id: UUID
    ) -> PatientForm:
        form.status = payload.status
        form.notes = payload.notes
        form.reviewed_at = datetime.now(UTC)
        form.reviewed_by_id = reviewer_id
        await self.db.flush()
        return form

    # ----------------------------------------------------
    # Consent Records
    # ----------------------------------------------------
    async def create_consent_record(
        self, clinic_id: UUID, payload: ConsentRecordCreate, ip_address: str | None = None
    ) -> ConsentRecord:
        consent = ConsentRecord(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            treatment_id=payload.treatment_id,
            consent_type=payload.consent_type,
            title=payload.title,
            content_text=payload.content_text,
            patient_signature=payload.patient_signature,
            signed_at=datetime.now(UTC),
            ip_address=ip_address,
            witness_name=payload.witness_name,
            expires_at=payload.expires_at,
            version=1,
        )
        self.db.add(consent)
        await self.db.flush()
        return consent

    async def get_consent_record(self, clinic_id: UUID, consent_id: UUID) -> ConsentRecord | None:
        stmt = (
            select(ConsentRecord)
            .options(
                selectinload(ConsentRecord.patient),
                selectinload(ConsentRecord.treatment),
            )
            .where(
                ConsentRecord.id == consent_id,
                ConsentRecord.clinic_id == clinic_id,
                ConsentRecord.deleted_at.is_(None),
            )
        )
        return await self.db.scalar(stmt)

    async def list_consent_records(
        self, clinic_id: UUID, patient_id: UUID | None = None
    ) -> list[ConsentRecord]:
        stmt = (
            select(ConsentRecord)
            .options(
                selectinload(ConsentRecord.patient),
                selectinload(ConsentRecord.treatment),
            )
            .where(
                ConsentRecord.clinic_id == clinic_id,
                ConsentRecord.deleted_at.is_(None),
            )
        )
        if patient_id:
            stmt = stmt.where(ConsentRecord.patient_id == patient_id)

        stmt = stmt.order_by(ConsentRecord.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
