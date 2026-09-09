from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.identity import AuditEvent, Role, User
from app.models.patient import Patient, PatientTimelineEvent
from app.models.prescription import (
    DosageFrequency,
    MedicineForm,
    PrescriptionStatus,
)
from app.models.treatment import Treatment
from app.repositories.prescription_repository import PrescriptionRepository
from app.schemas.prescription import (
    MedicineCatalogCreate,
    MedicineCatalogRead,
    PrescriptionCreate,
    PrescriptionDashboardStats,
    PrescriptionDetail,
    PrescriptionItemCreate,
    PrescriptionTemplateCreate,
    PrescriptionTemplateRead,
    PrescriptionUpdate,
)


class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PrescriptionRepository(db)

    async def _validate_entities(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        treatment_id: UUID,
        appointment_id: UUID,
        dentist_id: UUID,
        items: list[PrescriptionItemCreate],
        issue_immediately: bool = False,
    ) -> tuple[Patient, Treatment, Appointment, User]:
        # 1. Validate Patient
        patient_q = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        patient_res = await self.db.execute(patient_q)
        patient = patient_res.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found in this clinic.",
            )

        # 2. Validate Treatment
        treatment_q = select(Treatment).where(
            Treatment.id == treatment_id,
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
        )
        treatment_res = await self.db.execute(treatment_q)
        treatment = treatment_res.scalar_one_or_none()
        if not treatment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment record not found in this clinic.",
            )

        if treatment.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Treatment record does not belong to the specified patient.",
            )

        # 3. Validate Appointment
        appointment_q = select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == clinic_id,
            Appointment.deleted_at.is_(None),
        )
        appointment_res = await self.db.execute(appointment_q)
        appointment = appointment_res.scalar_one_or_none()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment record not found in this clinic.",
            )

        if appointment.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment does not belong to the specified patient.",
            )

        # 4. Validate Dentist
        dentist_q = select(User).where(
            User.id == dentist_id,
            User.clinic_id == clinic_id,
            User.deleted_at.is_(None),
        )
        dentist_res = await self.db.execute(dentist_q)
        dentist = dentist_res.scalar_one_or_none()
        if not dentist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescribing dentist not found in this clinic.",
            )

        if dentist.role not in [Role.DENTIST, Role.CLINIC_ADMIN, Role.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have clinical prescribing privileges.",
            )

        # 5. Validate Duplicate Medicines
        self._check_duplicate_medicines(items)

        # 6. Validate Empty Prescription if issuing immediately
        if issue_immediately and not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot issue an empty prescription without medications.",
            )

        return patient, treatment, appointment, dentist

    def _check_duplicate_medicines(self, items: list[PrescriptionItemCreate] | None):
        if not items:
            return
        seen_names = set()
        for it in items:
            clean_name = it.medicine_name.strip().lower()
            if clean_name in seen_names:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate medicine entry detected: '{it.medicine_name}'.",
                )
            seen_names.add(clean_name)

    async def create_prescription(
        self, clinic_id: UUID, payload: PrescriptionCreate, actor: User
    ) -> PrescriptionDetail:
        patient, treatment, _appointment, dentist = await self._validate_entities(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            treatment_id=payload.treatment_id,
            appointment_id=payload.appointment_id,
            dentist_id=payload.dentist_id,
            items=payload.items,
            issue_immediately=payload.issue_immediately,
        )

        # Generate unique prescription number
        rx_number = await self.repo.generate_prescription_number(clinic_id, payload.date)

        rx = await self.repo.create(clinic_id, payload, actor, rx_number)

        # Timeline Event
        event_type = (
            "PRESCRIPTION_ISSUED" if rx.status == PrescriptionStatus.ISSUED else "PRESCRIPTION_CREATED"
        )
        title = (
            f"Prescription #{rx_number} Issued"
            if rx.status == PrescriptionStatus.ISSUED
            else f"Prescription #{rx_number} Drafted"
        )
        self.db.add(
            PatientTimelineEvent(
                patient_id=patient.id,
                clinic_id=clinic_id,
                event_type=event_type,
                title=title,
                description=(
                    f"Clinician: Dr. {dentist.first_name} {dentist.last_name}. "
                    f"Diagnosis: {payload.diagnosis}. "
                    f"{len(payload.items)} medication(s) prescribed."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="PRESCRIPTION",
                entity_id=str(rx.id),
                metadata_json=json.dumps(
                    {
                        "prescription_number": rx_number,
                        "patient_id": str(patient.id),
                        "treatment_id": str(treatment.id),
                        "status": rx.status,
                        "item_count": len(payload.items),
                    }
                ),
            )
        )

        await self.db.commit()

        loaded_rx = await self.repo.get_by_id(clinic_id, rx.id)
        if not loaded_rx:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load created prescription.",
            )
        return self.repo.to_detail_schema(loaded_rx)

    async def get_prescription(
        self, clinic_id: UUID, prescription_id: UUID
    ) -> PrescriptionDetail:
        rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found.",
            )
        return self.repo.to_detail_schema(rx)

    async def update_prescription(
        self,
        clinic_id: UUID,
        prescription_id: UUID,
        payload: PrescriptionUpdate,
        actor: User,
    ) -> PrescriptionDetail:
        rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found.",
            )

        if rx.status == PrescriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled prescriptions cannot be modified.",
            )

        if rx.status == PrescriptionStatus.ISSUED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Prescription is officially ISSUED and locked for clinical immutability. "
                    "To modify, cancel this prescription with a reason or duplicate it to create an audited revision."
                ),
            )

        if payload.items is not None:
            self._check_duplicate_medicines(payload.items)

        updated_rx = await self.repo.update(rx, payload, actor)

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=rx.patient_id,
                clinic_id=clinic_id,
                event_type="PRESCRIPTION_MODIFIED",
                title=f"Prescription #{rx.prescription_number} Modified",
                description=f"Draft prescription updated by Dr. {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="PRESCRIPTION",
                entity_id=str(rx.id),
                metadata_json=json.dumps(
                    {
                        "prescription_number": rx.prescription_number,
                        "version": updated_rx.version,
                    }
                ),
            )
        )

        await self.db.commit()

        reloaded = await self.repo.get_by_id(clinic_id, rx.id)
        if not reloaded:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload modified prescription.",
            )
        return self.repo.to_detail_schema(reloaded)

    async def issue_prescription(
        self, clinic_id: UUID, prescription_id: UUID, actor: User
    ) -> PrescriptionDetail:
        rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found.",
            )

        if rx.status == PrescriptionStatus.ISSUED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription is already officially issued.",
            )

        if rx.status == PrescriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot issue a cancelled prescription.",
            )

        if not rx.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot issue an empty prescription without medications.",
            )

        issued_rx = await self.repo.issue(rx, actor)

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=rx.patient_id,
                clinic_id=clinic_id,
                event_type="PRESCRIPTION_ISSUED",
                title=f"Prescription #{rx.prescription_number} Officially Issued",
                description=(
                    f"Prescription finalized by Dr. {actor.first_name} {actor.last_name}. "
                    f"{len(rx.items)} medication(s) authorized."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="ISSUE",
                entity_type="PRESCRIPTION",
                entity_id=str(rx.id),
                metadata_json=json.dumps(
                    {
                        "prescription_number": rx.prescription_number,
                        "issued_at": str(issued_rx.issued_at),
                    }
                ),
            )
        )

        await self.db.commit()

        reloaded = await self.repo.get_by_id(clinic_id, rx.id)
        if not reloaded:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload issued prescription.",
            )
        return self.repo.to_detail_schema(reloaded)

    async def cancel_prescription(
        self, clinic_id: UUID, prescription_id: UUID, reason: str, actor: User
    ) -> PrescriptionDetail:
        rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found.",
            )

        if rx.status == PrescriptionStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription is already cancelled.",
            )

        await self.repo.cancel(rx, reason, actor)

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=rx.patient_id,
                clinic_id=clinic_id,
                event_type="PRESCRIPTION_CANCELLED",
                title=f"Prescription #{rx.prescription_number} Cancelled",
                description=f"Reason: {reason}. Cancelled by Dr. {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CANCEL",
                entity_type="PRESCRIPTION",
                entity_id=str(rx.id),
                metadata_json=json.dumps(
                    {
                        "prescription_number": rx.prescription_number,
                        "cancellation_reason": reason,
                    }
                ),
            )
        )

        await self.db.commit()

        reloaded = await self.repo.get_by_id(clinic_id, rx.id)
        if not reloaded:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload cancelled prescription.",
            )
        return self.repo.to_detail_schema(reloaded)

    async def duplicate_prescription(
        self, clinic_id: UUID, prescription_id: UUID, actor: User
    ) -> PrescriptionDetail:
        source_rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not source_rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source prescription not found.",
            )

        # Build duplicate payload
        items_payload = [
            PrescriptionItemCreate(
                medicine_name=item.medicine_name,
                generic_name=item.generic_name,
                brand_name=item.brand_name,
                strength=item.strength,
                form=item.form or MedicineForm.TABLET,
                dosage=item.dosage,
                route=item.route or "Oral",
                frequency=item.frequency or DosageFrequency.BD,
                duration=item.duration,
                quantity=item.quantity or 10,
                timing=item.timing,
                food_instructions=item.food_instructions,
                notes=item.notes,
            )
            for item in (source_rx.items or [])
            if item.deleted_at is None
        ]

        duplicate_payload = PrescriptionCreate(
            patient_id=source_rx.patient_id,
            treatment_id=source_rx.treatment_id,
            appointment_id=source_rx.appointment_id,
            dentist_id=actor.id,
            date=datetime.now(UTC).date(),
            diagnosis=source_rx.diagnosis,
            notes=f"Duplicated from {source_rx.prescription_number}. {source_rx.notes or ''}".strip(),
            instructions=source_rx.instructions,
            follow_up_date=None,
            items=items_payload,
            issue_immediately=False,
        )

        return await self.create_prescription(clinic_id, duplicate_payload, actor)

    async def delete_prescription(
        self, clinic_id: UUID, prescription_id: UUID, actor: User
    ) -> None:
        rx = await self.repo.get_by_id(clinic_id, prescription_id)
        if not rx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found.",
            )

        if rx.status == PrescriptionStatus.ISSUED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Issued prescriptions cannot be deleted. Use cancellation to maintain clinical audit integrity.",
            )

        await self.repo.soft_delete(rx, actor)

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="DELETE",
                entity_type="PRESCRIPTION",
                entity_id=str(rx.id),
                metadata_json=json.dumps(
                    {
                        "prescription_number": rx.prescription_number,
                    }
                ),
            )
        )
        await self.db.commit()

    async def list_prescriptions(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        treatment_id: UUID | None = None,
        dentist_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PrescriptionDetail]:
        records = await self.repo.list_prescriptions(
            clinic_id=clinic_id,
            patient_id=patient_id,
            treatment_id=treatment_id,
            dentist_id=dentist_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            search=search,
            limit=limit,
            offset=offset,
        )
        return [self.repo.to_detail_schema(rx) for rx in records]

    async def get_patient_prescriptions(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[PrescriptionDetail]:
        records = await self.repo.get_by_patient(clinic_id, patient_id)
        return [self.repo.to_detail_schema(rx) for rx in records]

    async def get_treatment_prescriptions(
        self, clinic_id: UUID, treatment_id: UUID
    ) -> list[PrescriptionDetail]:
        records = await self.repo.get_by_treatment(clinic_id, treatment_id)
        return [self.repo.to_detail_schema(rx) for rx in records]

    async def get_appointment_prescriptions(
        self, clinic_id: UUID, appointment_id: UUID
    ) -> list[PrescriptionDetail]:
        records = await self.repo.get_by_appointment(clinic_id, appointment_id)
        return [self.repo.to_detail_schema(rx) for rx in records]

    async def search_medicines(
        self,
        clinic_id: UUID | None = None,
        query: str | None = None,
        category: str | None = None,
        form: str | None = None,
        limit: int = 30,
    ) -> list[MedicineCatalogRead]:
        records = await self.repo.search_medicines(
            clinic_id=clinic_id,
            query=query,
            category=category,
            form=form,
            limit=limit,
        )
        return [MedicineCatalogRead.model_validate(m) for m in records]

    async def create_medicine(
        self, clinic_id: UUID, payload: MedicineCatalogCreate, actor: User
    ) -> MedicineCatalogRead:
        record = await self.repo.create_medicine(clinic_id, payload, actor)
        await self.db.commit()
        return MedicineCatalogRead.model_validate(record)

    async def list_templates(
        self, clinic_id: UUID | None = None, category: str | None = None
    ) -> list[PrescriptionTemplateRead]:
        records = await self.repo.list_templates(clinic_id=clinic_id, category=category)
        return [PrescriptionTemplateRead.model_validate(t) for t in records]

    async def create_template(
        self, clinic_id: UUID, payload: PrescriptionTemplateCreate, actor: User
    ) -> PrescriptionTemplateRead:
        record = await self.repo.create_template(clinic_id, payload, actor)
        await self.db.commit()
        return PrescriptionTemplateRead.model_validate(record)

    async def get_dashboard_stats(self, clinic_id: UUID) -> PrescriptionDashboardStats:
        return await self.repo.get_dashboard_stats(clinic_id)
