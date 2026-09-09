from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.treatment import (
    FollowUpStatus,
    Treatment,
    TreatmentFollowUp,
    TreatmentProcedure,
    TreatmentStatus,
)
from app.schemas.treatment import (
    FollowUpRead,
    ProcedureRead,
    TreatmentCreate,
    TreatmentDashboardStats,
    TreatmentDetail,
    TreatmentRead,
    TreatmentUpdate,
)


class TreatmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self, clinic_id: UUID):
        return (
            select(Treatment)
            .where(
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
            .options(
                selectinload(Treatment.patient).selectinload(Patient.medical_history),
                selectinload(Treatment.dentist),
                selectinload(Treatment.appointment),
                selectinload(Treatment.procedures),
                selectinload(Treatment.follow_ups),
            )
        )

    async def generate_treatment_number(
        self, clinic_id: UUID, target_date: date | None = None
    ) -> str:
        d = target_date or datetime.now(UTC).date()
        prefix = f"TRT-{d.strftime('%Y%m%d')}"
        query = select(func.count(Treatment.id)).where(
            Treatment.clinic_id == clinic_id,
            Treatment.treatment_number.like(f"{prefix}-%"),
        )
        res = await self.db.execute(query)
        count = res.scalar_one() or 0
        return f"{prefix}-{count + 1:04d}"

    async def get_by_id(self, clinic_id: UUID, treatment_id: UUID) -> Treatment | None:
        query = self._base_query(clinic_id).where(Treatment.id == treatment_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def get_active_by_appointment(
        self, clinic_id: UUID, appointment_id: UUID
    ) -> Treatment | None:
        query = self._base_query(clinic_id).where(
            Treatment.appointment_id == appointment_id,
            Treatment.status != TreatmentStatus.CANCELLED,
            Treatment.deleted_at.is_(None),
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def get_by_appointment(
        self, clinic_id: UUID, appointment_id: UUID
    ) -> Treatment | None:
        query = (
            self._base_query(clinic_id)
            .where(Treatment.appointment_id == appointment_id)
            .order_by(Treatment.created_at.desc())
        )
        res = await self.db.execute(query)
        return res.scalars().first()

    async def list_by_patient(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[Treatment]:
        query = (
            self._base_query(clinic_id)
            .where(Treatment.patient_id == patient_id)
            .order_by(Treatment.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

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
    ) -> list[Treatment]:
        query = self._base_query(clinic_id)

        if isinstance(status, TreatmentStatus):
            query = query.where(Treatment.status == status)
        elif isinstance(status, str) and status != "ALL":
            try:
                query = query.where(Treatment.status == TreatmentStatus(status))
            except ValueError:
                pass

        if isinstance(dentist_id, UUID):
            query = query.where(Treatment.dentist_id == dentist_id)

        if isinstance(patient_id, UUID):
            query = query.where(Treatment.patient_id == patient_id)

        if isinstance(target_date, date):
            query = query.where(func.date(Treatment.created_at) == target_date)

        if isinstance(search, str) and search.strip():
            term = f"%{search.strip()}%"
            query = query.join(Treatment.patient).where(
                or_(
                    Treatment.treatment_number.ilike(term),
                    Treatment.diagnosis.ilike(term),
                    Patient.first_name.ilike(term),
                    Patient.last_name.ilike(term),
                    Patient.mobile_number.ilike(term),
                    Patient.patient_number.ilike(term),
                )
            )

        query = query.order_by(Treatment.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create(
        self,
        clinic_id: UUID,
        payload: TreatmentCreate,
        treatment_number: str,
        user_id: UUID | None = None,
    ) -> Treatment:
        treatment = Treatment(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            dentist_id=payload.dentist_id,
            treatment_number=treatment_number,
            diagnosis=payload.diagnosis,
            chief_complaint=payload.chief_complaint,
            clinical_findings=payload.clinical_findings,
            treatment_plan=payload.treatment_plan,
            procedure_performed=payload.procedure_performed,
            local_anaesthesia_used=payload.local_anaesthesia_used,
            medicines_used=payload.medicines_used,
            clinical_notes=payload.clinical_notes,
            soap_subjective=payload.soap.subjective if payload.soap else None,
            soap_objective=payload.soap.objective if payload.soap else None,
            soap_assessment=payload.soap.assessment if payload.soap else None,
            soap_plan=payload.soap.plan if payload.soap else None,
            follow_up_instructions=payload.follow_up_instructions,
            status=payload.status,
            is_override=payload.is_override,
            created_by=user_id,
            updated_by=user_id,
        )

        for proc in payload.procedures:
            treatment.procedures.append(
                TreatmentProcedure(
                    id=uuid4(),
                    treatment_id=treatment.id,
                    procedure_name=proc.procedure_name,
                    tooth_number=proc.tooth_number,
                    quantity=proc.quantity,
                    cost=proc.cost,
                    duration=proc.duration,
                    notes=proc.notes,
                    status=proc.status,
                    created_by=user_id,
                )
            )

        if payload.follow_up:
            treatment.follow_ups.append(
                TreatmentFollowUp(
                    id=uuid4(),
                    treatment_id=treatment.id,
                    clinic_id=clinic_id,
                    patient_id=payload.patient_id,
                    follow_up_date=payload.follow_up.follow_up_date,
                    reason=payload.follow_up.reason,
                    instructions=payload.follow_up.instructions,
                    status=payload.follow_up.status,
                    created_by=user_id,
                )
            )

        self.db.add(treatment)
        await self.db.flush()
        return treatment

    async def update(
        self,
        treatment: Treatment,
        payload: TreatmentUpdate,
        user_id: UUID | None = None,
    ) -> Treatment:
        if payload.diagnosis is not None:
            treatment.diagnosis = payload.diagnosis
        if payload.chief_complaint is not None:
            treatment.chief_complaint = payload.chief_complaint
        if payload.clinical_findings is not None:
            treatment.clinical_findings = payload.clinical_findings
        if payload.treatment_plan is not None:
            treatment.treatment_plan = payload.treatment_plan
        if payload.procedure_performed is not None:
            treatment.procedure_performed = payload.procedure_performed
        if payload.local_anaesthesia_used is not None:
            treatment.local_anaesthesia_used = payload.local_anaesthesia_used
        if payload.medicines_used is not None:
            treatment.medicines_used = payload.medicines_used
        if payload.clinical_notes is not None:
            treatment.clinical_notes = payload.clinical_notes

        if payload.soap is not None:
            if payload.soap.subjective is not None:
                treatment.soap_subjective = payload.soap.subjective
            if payload.soap.objective is not None:
                treatment.soap_objective = payload.soap.objective
            if payload.soap.assessment is not None:
                treatment.soap_assessment = payload.soap.assessment
            if payload.soap.plan is not None:
                treatment.soap_plan = payload.soap.plan

        if payload.follow_up_instructions is not None:
            treatment.follow_up_instructions = payload.follow_up_instructions
        if payload.status is not None:
            treatment.status = payload.status

        if payload.procedures is not None:
            # Replace existing procedures with new set
            treatment.procedures.clear()
            for proc in payload.procedures:
                treatment.procedures.append(
                    TreatmentProcedure(
                        id=uuid4(),
                        treatment_id=treatment.id,
                        procedure_name=proc.procedure_name,
                        tooth_number=proc.tooth_number,
                        quantity=proc.quantity,
                        cost=proc.cost,
                        duration=proc.duration,
                        notes=proc.notes,
                        status=proc.status,
                        created_by=user_id,
                    )
                )

        if payload.follow_up is not None:
            treatment.follow_ups.append(
                TreatmentFollowUp(
                    id=uuid4(),
                    treatment_id=treatment.id,
                    clinic_id=treatment.clinic_id,
                    patient_id=treatment.patient_id,
                    follow_up_date=payload.follow_up.follow_up_date,
                    reason=payload.follow_up.reason,
                    instructions=payload.follow_up.instructions,
                    status=payload.follow_up.status,
                    created_by=user_id,
                )
            )

        treatment.updated_by = user_id
        await self.db.flush()
        return treatment

    async def complete(
        self,
        treatment: Treatment,
        notes: str | None = None,
        user_id: UUID | None = None,
    ) -> Treatment:
        treatment.status = TreatmentStatus.COMPLETED
        treatment.completed_at = datetime.now(UTC)
        if notes:
            treatment.clinical_notes = (
                f"{treatment.clinical_notes or ''}\n\n[Completion Note]: {notes}".strip()
            )
        treatment.updated_by = user_id
        await self.db.flush()
        return treatment

    async def cancel(
        self,
        treatment: Treatment,
        reason: str,
        user_id: UUID | None = None,
    ) -> Treatment:
        treatment.status = TreatmentStatus.CANCELLED
        treatment.cancellation_reason = reason
        treatment.updated_by = user_id
        await self.db.flush()
        return treatment

    async def soft_delete(
        self,
        treatment: Treatment,
        user_id: UUID | None = None,
    ) -> Treatment:
        treatment.deleted_at = datetime.now(UTC)
        treatment.updated_by = user_id
        await self.db.flush()
        return treatment

    async def get_dashboard_stats(self, clinic_id: UUID) -> TreatmentDashboardStats:
        planned_q = select(func.count(Treatment.id)).where(
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
            Treatment.status == TreatmentStatus.PLANNED,
        )
        in_prog_q = select(func.count(Treatment.id)).where(
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
            Treatment.status == TreatmentStatus.IN_PROGRESS,
        )
        completed_q = select(func.count(Treatment.id)).where(
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
            Treatment.status == TreatmentStatus.COMPLETED,
        )
        total_q = select(func.count(Treatment.id)).where(
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
        )

        today = datetime.now(UTC).date()
        next_week = today + timedelta(days=7)
        followups_q = select(func.count(TreatmentFollowUp.id)).where(
            TreatmentFollowUp.clinic_id == clinic_id,
            TreatmentFollowUp.status == FollowUpStatus.SCHEDULED,
            TreatmentFollowUp.follow_up_date <= next_week,
        )

        planned = (await self.db.execute(planned_q)).scalar_one() or 0
        in_progress = (await self.db.execute(in_prog_q)).scalar_one() or 0
        completed = (await self.db.execute(completed_q)).scalar_one() or 0
        total = (await self.db.execute(total_q)).scalar_one() or 0
        follow_ups_due = (await self.db.execute(followups_q)).scalar_one() or 0

        return TreatmentDashboardStats(
            planned=planned,
            in_progress=in_progress,
            completed=completed,
            follow_ups_due=follow_ups_due,
            total_treatments=total,
        )

    def to_read_model(self, treatment: Treatment) -> TreatmentRead:
        patient = treatment.patient
        dentist = treatment.dentist
        appointment = treatment.appointment

        patient_name = f"{patient.first_name} {patient.last_name}".strip() if patient else None
        dentist_name = (
            f"{dentist.first_name} {dentist.last_name}".strip() if dentist else None
        )

        procs = treatment.procedures or []
        total_cost = sum(float(p.cost or 0.0) * p.quantity for p in procs)

        return TreatmentRead(
            id=treatment.id,
            clinic_id=treatment.clinic_id,
            patient_id=treatment.patient_id,
            appointment_id=treatment.appointment_id,
            dentist_id=treatment.dentist_id,
            treatment_number=treatment.treatment_number,
            diagnosis=treatment.diagnosis,
            chief_complaint=treatment.chief_complaint,
            clinical_findings=treatment.clinical_findings,
            treatment_plan=treatment.treatment_plan,
            procedure_performed=treatment.procedure_performed,
            status=treatment.status,
            is_override=bool(getattr(treatment, "is_override", False) or False),
            created_at=getattr(treatment, "created_at", None) or datetime.now(UTC),
            completed_at=treatment.completed_at,
            patient_name=patient_name,
            patient_number=getattr(patient, "patient_number", None) if patient else None,
            patient_phone=getattr(patient, "mobile_number", None) if patient else None,
            dentist_name=dentist_name,
            appointment_number=getattr(appointment, "appointment_number", None)
            if appointment
            else None,
            appointment_date=getattr(appointment, "date", None) if appointment else None,
            procedures_count=len(procs),
            total_cost=round(total_cost, 2),
        )

    def to_detail_model(self, treatment: Treatment) -> TreatmentDetail:
        read_model = self.to_read_model(treatment)

        patient = treatment.patient
        alerts: list[str] = []
        if patient and getattr(patient, "medical_history", None):
            mh = patient.medical_history
            if getattr(mh, "cardiac_disease", False):
                alerts.append("Cardiac Disease")
            if getattr(mh, "hypertension", False):
                alerts.append("Hypertension")
            if getattr(mh, "diabetes", False):
                alerts.append("Diabetes")
            if getattr(mh, "pregnancy", False):
                alerts.append("Pregnancy")
            if getattr(mh, "allergies", None):
                alerts.append(f"Allergies: {mh.allergies}")
            if getattr(mh, "infectious_diseases", None):
                alerts.append(f"Infectious: {mh.infectious_diseases}")

        procedures_read = [
            ProcedureRead.model_validate(p) for p in (treatment.procedures or [])
        ]
        follow_ups_read = [
            FollowUpRead.model_validate(f) for f in (treatment.follow_ups or [])
        ]

        return TreatmentDetail(
            **read_model.model_dump(),
            local_anaesthesia_used=treatment.local_anaesthesia_used,
            medicines_used=treatment.medicines_used,
            clinical_notes=treatment.clinical_notes,
            soap_subjective=treatment.soap_subjective,
            soap_objective=treatment.soap_objective,
            soap_assessment=treatment.soap_assessment,
            soap_plan=treatment.soap_plan,
            follow_up_instructions=treatment.follow_up_instructions,
            cancellation_reason=treatment.cancellation_reason,
            procedures=procedures_read,
            follow_ups=follow_ups_read,
            patient_medical_alerts=alerts,
        )
