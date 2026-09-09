from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditEvent,
    DentalHistory,
    MedicalHistory,
    Patient,
    PatientDocument,
    PatientTimelineEvent,
    User,
)
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import DuplicateWarning, PatientInput, PatientUpdate


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

