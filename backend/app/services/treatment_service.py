from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentTimelineEvent,
)
from app.models.identity import AuditEvent, Role, User
from app.models.patient import Patient, PatientTimelineEvent
from app.models.treatment import TreatmentStatus
from app.repositories.treatment_repository import TreatmentRepository
from app.schemas.treatment import (
    TreatmentCancel,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentDashboardStats,
    TreatmentDetail,
    TreatmentRead,
    TreatmentUpdate,
)


class TreatmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TreatmentRepository(db)

    async def create_treatment(
        self,
        clinic_id: UUID,
        payload: TreatmentCreate,
        actor: User,
    ) -> TreatmentDetail:
        # 1. Validate Patient
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id or patient.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Patient not found in this clinic.")

        # 2. Validate Appointment
        appointment = await self.db.get(Appointment, payload.appointment_id)
        if not appointment or appointment.clinic_id != clinic_id or appointment.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Appointment not found in this clinic.")

        if appointment.patient_id != payload.patient_id:
            raise HTTPException(
                status_code=400,
                detail="Appointment does not belong to this patient.",
            )

        # 3. Validate Dentist
        dentist = await self.db.get(User, payload.dentist_id)
        if not dentist or (dentist.clinic_id != clinic_id and dentist.role != Role.SUPER_ADMIN):
            raise HTTPException(status_code=404, detail="Clinician not found in this clinic.")

        # 4. Check One Active Treatment Rule
        existing_active = await self.repo.get_active_by_appointment(
            clinic_id, payload.appointment_id
        )
        if existing_active and not payload.is_override:
            raise HTTPException(
                status_code=400,
                detail="An active treatment already exists for this appointment. Admin override required to create another.",
            )

        if (
            existing_active
            and payload.is_override
            and actor.role not in (Role.CLINIC_ADMIN, Role.SUPER_ADMIN)
        ):
            raise HTTPException(
                status_code=403,
                detail="Only clinic administrators can override active treatments on an appointment.",
            )

        # 5. Validate Follow-Up Date
        if payload.follow_up and payload.follow_up.follow_up_date < appointment.date:
            raise HTTPException(
                status_code=400,
                detail="Follow-up date cannot be before the treatment date.",
            )

        # 6. Generate Treatment Number
        treatment_number = await self.repo.generate_treatment_number(
            clinic_id, appointment.date
        )

        # 7. Create Treatment Record
        treatment = await self.repo.create(clinic_id, payload, treatment_number, actor.id)

        # 8. Sync Appointment Status -> IN_TREATMENT
        if appointment.status in (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED, AppointmentStatus.CHECKED_IN):
            prev_status = appointment.status.value
            appointment.status = AppointmentStatus.IN_TREATMENT
            if not appointment.start_datetime:
                appointment.start_datetime = datetime.now(UTC)

            self.db.add(
                AppointmentTimelineEvent(
                    appointment_id=appointment.id,
                    clinic_id=clinic_id,
                    from_status=prev_status,
                    to_status=AppointmentStatus.IN_TREATMENT.value,
                    event_type="TREATMENT_STARTED",
                    title=f"Treatment #{treatment_number} Initiated",
                    notes=f"Diagnosis: {payload.diagnosis}",
                    actor_id=actor.id,
                )
            )

        # 9. Dual Timeline: Patient Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=patient.id,
                clinic_id=clinic_id,
                event_type="TREATMENT_CREATED",
                title=f"Treatment #{treatment_number} Created",
                description=(
                    f"Diagnosis: {payload.diagnosis}. "
                    f"Clinician: Dr. {dentist.first_name} {dentist.last_name}. "
                    f"{len(payload.procedures)} procedure(s) planned/recorded."
                ),
                actor_id=actor.id,
            )
        )

        # 10. Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps(
                    {
                        "treatment_number": treatment_number,
                        "patient_id": str(patient.id),
                        "appointment_id": str(appointment.id),
                        "dentist_id": str(dentist.id),
                        "diagnosis": payload.diagnosis,
                        "is_override": payload.is_override,
                    }
                ),
            )
        )

        # 11. Synchronize Procedures with Odontogram
        from app.services.odontogram_service import OdontogramService

        odontogram_svc = OdontogramService(self.db)
        for proc in treatment.procedures:
            if proc.tooth_number:
                await odontogram_svc.sync_treatment_procedure(
                    clinic_id=clinic_id,
                    patient_id=patient.id,
                    tooth_number_raw=proc.tooth_number,
                    procedure_name=proc.procedure_name,
                    procedure_id=proc.id,
                    treatment_id=treatment.id,
                    appointment_id=appointment.id,
                    actor=actor,
                )

        await self.db.commit()

        # Reload with relationships
        full_treatment = await self.repo.get_by_id(clinic_id, treatment.id)
        return self.repo.to_detail_model(full_treatment or treatment)

    async def get_treatment(self, clinic_id: UUID, treatment_id: UUID) -> TreatmentDetail:
        treatment = await self.repo.get_by_id(clinic_id, treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")
        return self.repo.to_detail_model(treatment)

    async def update_treatment(
        self,
        clinic_id: UUID,
        treatment_id: UUID,
        payload: TreatmentUpdate,
        actor: User,
    ) -> TreatmentDetail:
        treatment = await self.repo.get_by_id(clinic_id, treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        # Immutability check
        if treatment.status == TreatmentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Completed treatments are permanently locked and cannot be edited.",
            )
        if treatment.status == TreatmentStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="Cancelled treatments cannot be edited.",
            )

        # Validate follow-up date if updated
        if (
            payload.follow_up
            and treatment.appointment
            and payload.follow_up.follow_up_date < treatment.appointment.date
        ):
            raise HTTPException(
                status_code=400,
                detail="Follow-up date cannot be before the treatment date.",
            )

        updated = await self.repo.update(treatment, payload, actor.id)

        # Patient timeline update
        self.db.add(
            PatientTimelineEvent(
                patient_id=treatment.patient_id,
                clinic_id=clinic_id,
                event_type="TREATMENT_UPDATED",
                title=f"Treatment #{treatment.treatment_number} Updated",
                description=f"Clinical record modified by Dr. {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        # Audit event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps(
                    {
                        "treatment_number": treatment.treatment_number,
                        "updated_fields": list(
                            payload.model_dump(exclude_unset=True).keys()
                        ),
                    }
                ),
            )
        )
        if payload.procedures is not None:
            from app.services.odontogram_service import OdontogramService

            odontogram_svc = OdontogramService(self.db)
            for proc in updated.procedures:
                if proc.tooth_number:
                    await odontogram_svc.sync_treatment_procedure(
                        clinic_id=clinic_id,
                        patient_id=treatment.patient_id,
                        tooth_number_raw=proc.tooth_number,
                        procedure_name=proc.procedure_name,
                        procedure_id=proc.id,
                        treatment_id=treatment.id,
                        appointment_id=treatment.appointment_id,
                        actor=actor,
                    )

        await self.db.commit()
        full = await self.repo.get_by_id(clinic_id, treatment.id)
        return self.repo.to_detail_model(full or updated)

    async def complete_treatment(
        self,
        clinic_id: UUID,
        treatment_id: UUID,
        payload: TreatmentComplete,
        actor: User,
    ) -> TreatmentDetail:
        treatment = await self.repo.get_by_id(clinic_id, treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        if treatment.status == TreatmentStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Treatment is already completed.")
        if treatment.status == TreatmentStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Cancelled treatment cannot be completed.")

        completed = await self.repo.complete(treatment, payload.notes, actor.id)

        # Complete linked appointment if requested
        if payload.complete_appointment and treatment.appointment:
            appt = treatment.appointment
            if appt.status != AppointmentStatus.COMPLETED:
                prev_status = appt.status.value
                appt.status = AppointmentStatus.COMPLETED
                appt.end_datetime = datetime.now(UTC)

                self.db.add(
                    AppointmentTimelineEvent(
                        appointment_id=appt.id,
                        clinic_id=clinic_id,
                        from_status=prev_status,
                        to_status=AppointmentStatus.COMPLETED.value,
                        event_type="APPOINTMENT_COMPLETED",
                        title=f"Appointment Completed with Treatment #{treatment.treatment_number}",
                        notes=payload.notes,
                        actor_id=actor.id,
                    )
                )

        # Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=treatment.patient_id,
                clinic_id=clinic_id,
                event_type="TREATMENT_COMPLETED",
                title=f"Treatment #{treatment.treatment_number} Completed",
                description=(
                    f"Treatment successfully completed by Dr. {treatment.dentist.first_name if treatment.dentist else actor.first_name}."
                ),
                actor_id=actor.id,
            )
        )

        # Audit event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="COMPLETE",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps(
                    {
                        "treatment_number": treatment.treatment_number,
                        "completed_appointment": payload.complete_appointment,
                    }
                ),
            )
        )

        await self.db.commit()
        full = await self.repo.get_by_id(clinic_id, treatment.id)
        return self.repo.to_detail_model(full or completed)

    async def cancel_treatment(
        self,
        clinic_id: UUID,
        treatment_id: UUID,
        payload: TreatmentCancel,
        actor: User,
    ) -> TreatmentDetail:
        treatment = await self.repo.get_by_id(clinic_id, treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        if treatment.status == TreatmentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Completed treatments are permanently locked and cannot be cancelled.",
            )

        cancelled = await self.repo.cancel(treatment, payload.reason, actor.id)

        # Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=treatment.patient_id,
                clinic_id=clinic_id,
                event_type="TREATMENT_CANCELLED",
                title=f"Treatment #{treatment.treatment_number} Cancelled",
                description=f"Cancellation reason: {payload.reason}",
                actor_id=actor.id,
            )
        )

        # Audit event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CANCEL",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps(
                    {
                        "treatment_number": treatment.treatment_number,
                        "reason": payload.reason,
                    }
                ),
            )
        )

        await self.db.commit()
        full = await self.repo.get_by_id(clinic_id, treatment.id)
        return self.repo.to_detail_model(full or cancelled)

    async def delete_treatment(
        self, clinic_id: UUID, treatment_id: UUID, actor: User
    ) -> dict[str, str]:
        if actor.role not in (Role.CLINIC_ADMIN, Role.SUPER_ADMIN):
            raise HTTPException(
                status_code=403,
                detail="Only clinic administrators can delete treatment records.",
            )

        treatment = await self.repo.get_by_id(clinic_id, treatment_id)
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        if treatment.status == TreatmentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Completed treatments cannot be deleted.",
            )

        await self.repo.soft_delete(treatment, actor.id)

        # Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=treatment.patient_id,
                clinic_id=clinic_id,
                event_type="TREATMENT_DELETED",
                title=f"Treatment #{treatment.treatment_number} Deleted",
                description="Treatment record removed by clinic administrator.",
                actor_id=actor.id,
            )
        )

        # Audit event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="DELETE",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps(
                    {"treatment_number": treatment.treatment_number}
                ),
            )
        )

        await self.db.commit()
        return {"detail": "Treatment deleted successfully."}

    async def list_treatments(
        self,
        clinic_id: UUID,
        search: str | None = None,
        status: TreatmentStatus | None = None,
        dentist_id: UUID | None = None,
        patient_id: UUID | None = None,
        target_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TreatmentRead]:
        treatments = await self.repo.list_treatments(
            clinic_id=clinic_id,
            search=search,
            status=status,
            dentist_id=dentist_id,
            patient_id=patient_id,
            target_date=target_date,
            skip=skip,
            limit=limit,
        )
        return [self.repo.to_read_model(t) for t in treatments]

    async def list_by_patient(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[TreatmentRead]:
        treatments = await self.repo.list_by_patient(clinic_id, patient_id)
        return [self.repo.to_read_model(t) for t in treatments]

    async def get_by_appointment(
        self, clinic_id: UUID, appointment_id: UUID
    ) -> TreatmentDetail | None:
        treatment = await self.repo.get_by_appointment(clinic_id, appointment_id)
        if not treatment:
            return None
        return self.repo.to_detail_model(treatment)

    async def get_dashboard_stats(self, clinic_id: UUID) -> TreatmentDashboardStats:
        return await self.repo.get_dashboard_stats(clinic_id)
