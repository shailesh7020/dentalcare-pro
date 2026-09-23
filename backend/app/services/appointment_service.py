from __future__ import annotations

import json
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import (
    AppointmentStatus,
    Chair,
    ChairStatus,
    VisitType,
)
from app.models.identity import AuditEvent, Role, User
from app.models.patient import Patient, PatientTimelineEvent
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentDetail,
    AppointmentQueueItem,
    AppointmentRead,
    AppointmentReschedule,
    AppointmentUpdate,
    CalendarDayResponse,
    CalendarMonthResponse,
    CalendarWeekResponse,
    ChairRead,
    DashboardStatsResponse,
    DentistScheduleRead,
)
from app.services.notification_service import NotificationType, notification_service


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AppointmentRepository(db)

    @staticmethod
    def compute_end_time(start_time: time, duration: int) -> time:
        dummy_dt = datetime.combine(datetime.now(UTC).date(), start_time) + timedelta(minutes=duration)
        return dummy_dt.time()

    async def _validate_participants(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        dentist_id: UUID,
        chair_id: UUID,
    ) -> tuple[Patient, User, Chair]:
        # 1. Patient check
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id or patient.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found in this clinic or is archived",
            )

        # 2. Dentist check
        dentist = await self.db.get(User, dentist_id)
        if (
            not dentist
            or dentist.clinic_id != clinic_id
            or not dentist.is_active
            or dentist.deleted_at is not None
            or dentist.role != Role.DENTIST
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned dentist not found or does not have dentist privileges in this clinic",
            )

        # 3. Chair check
        chair = await self.db.get(Chair, chair_id)
        if not chair or chair.clinic_id != clinic_id or chair.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected dental chair not found in this clinic",
            )
        if chair.status != ChairStatus.ACTIVE or not chair.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dental chair '{chair.name}' is currently in maintenance or inactive",
            )

        return patient, dentist, chair

    async def _check_availability(
        self,
        clinic_id: UUID,
        dentist_id: UUID,
        chair_id: UUID,
        patient_id: UUID,
        target_date: date,
        start_time: time,
        end_time: time,
        is_emergency_override: bool,
        actor: User,
        exclude_id: UUID | None = None,
    ) -> None:
        conflicts = await self.repo.check_conflicts(
            clinic_id=clinic_id,
            dentist_id=dentist_id,
            chair_id=chair_id,
            patient_id=patient_id,
            target_date=target_date,
            start_time=start_time,
            end_time=end_time,
            exclude_id=exclude_id,
        )

        has_conflict = False
        conflict_msg = ""

        if conflicts["dentist_conflict"]:
            has_conflict = True
            c = conflicts["dentist_conflict"]
            conflict_msg = (
                f"Dentist conflict: Doctor already has appointment #{c.appointment_number} "
                f"scheduled from {c.start_time.strftime('%H:%M')} to {c.end_time.strftime('%H:%M')}."
            )
        elif conflicts["chair_conflict"]:
            has_conflict = True
            c = conflicts["chair_conflict"]
            conflict_msg = (
                f"Chair conflict: Chair is already reserved for appointment #{c.appointment_number} "
                f"from {c.start_time.strftime('%H:%M')} to {c.end_time.strftime('%H:%M')}."
            )
        elif conflicts["patient_conflict"]:
            has_conflict = True
            c = conflicts["patient_conflict"]
            conflict_msg = (
                f"Patient conflict: Patient already has appointment #{c.appointment_number} "
                f"from {c.start_time.strftime('%H:%M')} to {c.end_time.strftime('%H:%M')}."
            )
        elif conflicts["blocked_conflict"]:
            has_conflict = True
            c = conflicts["blocked_conflict"]
            conflict_msg = f"Dentist availability conflict: Time blocked for '{c.title}'."

        if has_conflict:
            # Check for Admin Emergency Override
            if is_emergency_override and actor.role in (Role.CLINIC_ADMIN, Role.SUPER_ADMIN):
                return  # Override permitted
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflict_msg or "Appointment slot conflict detected.",
            )

    async def create(
        self, clinic_id: UUID, payload: AppointmentCreate, actor: User
    ) -> AppointmentDetail:
        end_time = self.compute_end_time(payload.start_time, payload.duration)

        # 1. Validate participants
        patient, dentist, chair = await self._validate_participants(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            dentist_id=payload.dentist_id,
            chair_id=payload.chair_id,
        )

        # 2. Availability conflict check
        await self._check_availability(
            clinic_id=clinic_id,
            dentist_id=payload.dentist_id,
            chair_id=payload.chair_id,
            patient_id=payload.patient_id,
            target_date=payload.date,
            start_time=payload.start_time,
            end_time=end_time,
            is_emergency_override=payload.is_emergency_override,
            actor=actor,
        )

        # 3. Generate sequential appointment number (APT-YYYYMMDD-XXXX)
        today_count = await self.repo.count_today_appointments(clinic_id, payload.date)
        appointment_number = f"APT-{payload.date.strftime('%Y%m%d')}-{today_count + 1:04d}"

        # 4. Create appointment
        apt = await self.repo.create(
            clinic_id=clinic_id,
            appointment_number=appointment_number,
            payload=payload,
            end_time=end_time,
            actor_id=actor.id,
        )

        # 5. Dual Timeline: Append Patient Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=patient.id,
                clinic_id=clinic_id,
                event_type="APPOINTMENT_CREATED",
                title="Appointment Scheduled",
                description=(
                    f"Appointment #{appointment_number} ({payload.visit_type}) scheduled with "
                    f"Dr. {dentist.first_name} {dentist.last_name} on {payload.date} at "
                    f"{payload.start_time.strftime('%H:%M')} in {chair.name}."
                ),
                actor_id=actor.id,
            )
        )

        # 6. Audit event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="APPOINTMENT",
                entity_id=str(apt.id),
                metadata_json=json.dumps(
                    {
                        "appointment_number": appointment_number,
                        "date": str(payload.date),
                        "start_time": payload.start_time.strftime("%H:%M"),
                        "dentist_id": str(payload.dentist_id),
                        "chair_id": str(payload.chair_id),
                        "is_emergency_override": payload.is_emergency_override,
                    }
                ),
            )
        )

        # 7. Notification intent
        notification_service.dispatch_appointment_event(
            notification_type=NotificationType.CONFIRMATION,
            appointment=apt,
        )

        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, apt.id)
        return self.repo.to_detail_model(refreshed or apt)

    async def get(self, clinic_id: UUID, appointment_id: UUID) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found in this clinic",
            )
        return self.repo.to_detail_model(apt)

    async def update(
        self,
        clinic_id: UUID,
        appointment_id: UUID,
        payload: AppointmentUpdate,
        actor: User,
    ) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found in this clinic",
            )

        # Business Rule: Completed appointments cannot be edited
        if apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed appointments cannot be modified.",
            )

        new_date = payload.date or apt.date
        new_start = payload.start_time or apt.start_time
        new_duration = payload.duration or apt.duration
        new_end = self.compute_end_time(new_start, new_duration)
        new_dentist = payload.dentist_id or apt.dentist_id
        new_chair = payload.chair_id or apt.chair_id
        new_patient = payload.patient_id or apt.patient_id
        override = (
            payload.is_emergency_override
            if payload.is_emergency_override is not None
            else apt.is_emergency_override
        )

        # Re-check availability if slot parameters change
        if (
            new_date != apt.date
            or new_start != apt.start_time
            or new_end != apt.end_time
            or new_dentist != apt.dentist_id
            or new_chair != apt.chair_id
        ):
            await self._validate_participants(clinic_id, new_patient, new_dentist, new_chair)
            await self._check_availability(
                clinic_id=clinic_id,
                dentist_id=new_dentist,
                chair_id=new_chair,
                patient_id=new_patient,
                target_date=new_date,
                start_time=new_start,
                end_time=new_end,
                is_emergency_override=override,
                actor=actor,
                exclude_id=appointment_id,
            )

        updated_apt = await self.repo.update(
            appointment=apt, payload=payload, end_time=new_end, actor_id=actor.id
        )

        # Audit & Patient Timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=updated_apt.patient_id,
                clinic_id=clinic_id,
                event_type="APPOINTMENT_UPDATED",
                title="Appointment Details Updated",
                description=f"Appointment #{updated_apt.appointment_number} scheduling details updated.",
                actor_id=actor.id,
            )
        )
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
                metadata_json=json.dumps(payload.model_dump(exclude_unset=True, mode="json")),
            )
        )

        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated_apt.id)
        return self.repo.to_detail_model(refreshed or updated_apt)

    async def confirm(self, clinic_id: UUID, appointment_id: UUID, actor: User) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        if apt.status not in (AppointmentStatus.SCHEDULED, AppointmentStatus.RESCHEDULED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot confirm appointment with status '{apt.status}'",
            )

        updated = await self.repo.change_status(
            appointment=apt,
            new_status=AppointmentStatus.CONFIRMED,
            event_type="CONFIRMED",
            title="Appointment Confirmed",
            notes="Patient confirmed arrival schedule",
            actor_id=actor.id,
        )

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CONFIRM",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
            )
        )
        notification_service.dispatch_appointment_event(NotificationType.CONFIRMATION, updated)
        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def checkin(self, clinic_id: UUID, appointment_id: UUID, actor: User) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        if apt.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot check in appointment with status '{apt.status}'",
            )

        updated = await self.repo.change_status(
            appointment=apt,
            new_status=AppointmentStatus.CHECKED_IN,
            event_type="CHECKED_IN",
            title="Patient Checked In",
            notes="Patient has arrived at clinic reception and entered waiting queue",
            actor_id=actor.id,
        )

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CHECKIN",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
            )
        )
        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def start_treatment(
        self, clinic_id: UUID, appointment_id: UUID, actor: User
    ) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )

        updated = await self.repo.change_status(
            appointment=apt,
            new_status=AppointmentStatus.IN_TREATMENT,
            event_type="TREATMENT_STARTED",
            title="Treatment Started",
            notes="Patient seated in dental chair and procedure commenced",
            actor_id=actor.id,
        )

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="START_TREATMENT",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
            )
        )
        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def complete(
        self, clinic_id: UUID, appointment_id: UUID, actor: User
    ) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )

        updated = await self.repo.change_status(
            appointment=apt,
            new_status=AppointmentStatus.COMPLETED,
            event_type="COMPLETED",
            title="Appointment Completed",
            notes="Clinical treatment concluded; patient ready for checkout",
            actor_id=actor.id,
        )

        # Dual Timeline: Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=updated.patient_id,
                clinic_id=clinic_id,
                event_type="APPOINTMENT_COMPLETED",
                title="Appointment Completed",
                description=f"Appointment #{updated.appointment_number} completed successfully.",
                actor_id=actor.id,
            )
        )
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="COMPLETE",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
            )
        )
        notification_service.dispatch_appointment_event(NotificationType.FOLLOW_UP, updated)

        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def cancel(
        self, clinic_id: UUID, appointment_id: UUID, payload: AppointmentCancel, actor: User
    ) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        if apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed appointments cannot be cancelled.",
            )

        updated = await self.repo.change_status(
            appointment=apt,
            new_status=AppointmentStatus.CANCELLED,
            event_type="CANCELLED",
            title="Appointment Cancelled",
            cancellation_reason=payload.reason,
            actor_id=actor.id,
        )

        # Dual Timeline: Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=updated.patient_id,
                clinic_id=clinic_id,
                event_type="APPOINTMENT_CANCELLED",
                title="Appointment Cancelled",
                description=f"Appointment #{updated.appointment_number} cancelled. Reason: {payload.reason}",
                actor_id=actor.id,
            )
        )
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CANCEL",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
                metadata_json=json.dumps({"reason": payload.reason}),
            )
        )
        notification_service.dispatch_appointment_event(
            NotificationType.CANCELLATION, updated, extra_note=payload.reason
        )

        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def reschedule(
        self,
        clinic_id: UUID,
        appointment_id: UUID,
        payload: AppointmentReschedule,
        actor: User,
    ) -> AppointmentDetail:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        if apt.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed appointments cannot be rescheduled.",
            )

        duration = payload.duration or apt.duration
        new_end = self.compute_end_time(payload.new_start_time, duration)
        dentist_id = payload.new_dentist_id or apt.dentist_id
        chair_id = payload.new_chair_id or apt.chair_id

        # Availability check on target slot
        await self._check_availability(
            clinic_id=clinic_id,
            dentist_id=dentist_id,
            chair_id=chair_id,
            patient_id=apt.patient_id,
            target_date=payload.new_date,
            start_time=payload.new_start_time,
            end_time=new_end,
            is_emergency_override=payload.is_emergency_override,
            actor=actor,
            exclude_id=appointment_id,
        )

        updated = await self.repo.reschedule(
            appointment=apt,
            new_date=payload.new_date,
            new_start_time=payload.new_start_time,
            new_end_time=new_end,
            duration=duration,
            new_chair_id=chair_id,
            new_dentist_id=dentist_id,
            reason=payload.reason,
            is_emergency_override=payload.is_emergency_override,
            actor_id=actor.id,
        )

        # Dual Timeline: Patient timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=updated.patient_id,
                clinic_id=clinic_id,
                event_type="APPOINTMENT_RESCHEDULED",
                title="Appointment Rescheduled",
                description=(
                    f"Appointment #{updated.appointment_number} rescheduled to {payload.new_date} "
                    f"at {payload.new_start_time.strftime('%H:%M')}. Reason: {payload.reason}"
                ),
                actor_id=actor.id,
            )
        )
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="RESCHEDULE",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
                metadata_json=json.dumps(
                    {
                        "new_date": str(payload.new_date),
                        "new_start_time": payload.new_start_time.strftime("%H:%M"),
                        "reason": payload.reason,
                    }
                ),
            )
        )
        notification_service.dispatch_appointment_event(
            NotificationType.RESCHEDULE, updated, extra_note=payload.reason
        )

        await self.db.commit()
        refreshed = await self.repo.get(clinic_id, updated.id)
        return self.repo.to_detail_model(refreshed or updated)

    async def delete(self, clinic_id: UUID, appointment_id: UUID, actor: User) -> None:
        apt = await self.repo.get(clinic_id, appointment_id)
        if not apt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        apt.deleted_at = datetime.now(UTC)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="DELETE",
                entity_type="APPOINTMENT",
                entity_id=str(appointment_id),
            )
        )
        await self.db.commit()

    async def list(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        dentist_id: UUID | None = None,
        chair_id: UUID | None = None,
        target_date: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AppointmentStatus | None = None,
        visit_type: VisitType | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
        sort_asc: bool = True,
    ) -> list[AppointmentRead]:
        appointments = await self.repo.list(
            clinic_id=clinic_id,
            patient_id=patient_id,
            dentist_id=dentist_id,
            chair_id=chair_id,
            target_date=target_date,
            start_date=start_date,
            end_date=end_date,
            status=status,
            visit_type=visit_type,
            search=search,
            skip=skip,
            limit=limit,
            sort_asc=sort_asc,
        )
        return [self.repo.to_read_model(apt) for apt in appointments]

    async def get_day_calendar(self, clinic_id: UUID, target_date: date) -> CalendarDayResponse:
        chairs = await self.db.scalars(
            select(Chair)
            .where(Chair.clinic_id == clinic_id, Chair.deleted_at.is_(None))
            .order_by(Chair.name.asc())
        )
        chair_models = [ChairRead.model_validate(c) for c in chairs.all()]
        appointments = await self.repo.get_day_calendar(clinic_id, target_date)
        return CalendarDayResponse(
            date=target_date,
            chairs=chair_models,
            appointments=[self.repo.to_read_model(apt) for apt in appointments],
        )

    async def get_week_calendar(
        self, clinic_id: UUID, start_date: date, end_date: date
    ) -> CalendarWeekResponse:
        appointments = await self.repo.get_week_calendar(clinic_id, start_date, end_date)
        return CalendarWeekResponse(
            start_date=start_date,
            end_date=end_date,
            appointments=[self.repo.to_read_model(apt) for apt in appointments],
        )

    async def get_month_calendar(
        self, clinic_id: UUID, year: int, month: int
    ) -> CalendarMonthResponse:
        appointments = await self.repo.get_month_calendar(clinic_id, year, month)
        return CalendarMonthResponse(
            year=year,
            month=month,
            appointments=[self.repo.to_read_model(apt) for apt in appointments],
        )

    async def get_queue(self, clinic_id: UUID, target_date: date) -> list[AppointmentQueueItem]:
        return await self.repo.get_reception_queue(clinic_id, target_date)

    async def get_stats(self, clinic_id: UUID, target_date: date) -> DashboardStatsResponse:
        return await self.repo.get_dashboard_stats(clinic_id, target_date)

    async def get_dentist_schedule(
        self, clinic_id: UUID, dentist_id: UUID, start_date: date, end_date: date
    ) -> DentistScheduleRead:
        return await self.repo.get_dentist_schedule(clinic_id, dentist_id, start_date, end_date)
