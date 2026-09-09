from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentTimelineEvent,
    DentistBlockedTime,
    DentistWorkingHour,
    VisitType,
)
from app.models.identity import User
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentDetail,
    AppointmentQueueItem,
    AppointmentRead,
    AppointmentTimelineEventRead,
    AppointmentUpdate,
    BlockedTimeRead,
    DashboardStatsResponse,
    DentistScheduleRead,
    WorkingHourRead,
)


class AppointmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self, clinic_id: UUID):
        return (
            select(Appointment)
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.deleted_at.is_(None),
            )
            .options(
                selectinload(Appointment.patient).selectinload(Patient.medical_history),
                selectinload(Appointment.dentist),
                selectinload(Appointment.chair),
                selectinload(Appointment.timeline_events),
            )
        )

    def to_read_model(self, apt: Appointment) -> AppointmentRead:
        patient_name = None
        patient_number = None
        patient_phone = None
        if apt.patient:
            names = [apt.patient.first_name, apt.patient.middle_name, apt.patient.last_name]
            patient_name = " ".join(filter(None, names))
            patient_number = apt.patient.patient_number
            patient_phone = apt.patient.mobile_number

        dentist_name = None
        if apt.dentist:
            dentist_name = f"Dr. {apt.dentist.first_name} {apt.dentist.last_name}"

        chair_name = apt.chair.name if apt.chair else None

        return AppointmentRead(
            id=apt.id,
            clinic_id=apt.clinic_id,
            patient_id=apt.patient_id,
            dentist_id=apt.dentist_id,
            chair_id=apt.chair_id,
            appointment_number=apt.appointment_number,
            date=apt.date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            duration=apt.duration,
            status=getattr(apt, "status", None) or AppointmentStatus.SCHEDULED,
            visit_type=getattr(apt, "visit_type", None) or VisitType.CONSULTATION,
            priority=getattr(apt, "priority", None) or "NORMAL",
            chief_complaint=getattr(apt, "chief_complaint", None),
            notes=getattr(apt, "notes", None),
            cancellation_reason=getattr(apt, "cancellation_reason", None),
            is_emergency_override=bool(getattr(apt, "is_emergency_override", False)),
            created_at=getattr(apt, "created_at", None) or datetime.now(UTC),
            updated_at=getattr(apt, "updated_at", None) or datetime.now(UTC),
            patient_name=patient_name,
            patient_number=patient_number,
            patient_phone=patient_phone,
            dentist_name=dentist_name,
            chair_name=chair_name,
        )

    def to_detail_model(self, apt: Appointment) -> AppointmentDetail:
        read_model = self.to_read_model(apt)
        medical_alerts: list[str] = []
        patient_photo_url = None
        if apt.patient:
            patient_photo_url = apt.patient.photo_url
            med = apt.patient.medical_history
            if med:
                if med.cardiac_disease:
                    medical_alerts.append("Cardiac Disease")
                if med.hypertension:
                    medical_alerts.append("Hypertension")
                if med.diabetes:
                    medical_alerts.append("Diabetes")
                if med.asthma:
                    medical_alerts.append("Asthma")
                if med.epilepsy:
                    medical_alerts.append("Epilepsy")
                if med.pregnancy:
                    medical_alerts.append("Pregnancy")
                if med.allergies:
                    medical_alerts.append(f"Allergy: {med.allergies}")

        timeline_events = [
            AppointmentTimelineEventRead(
                id=event.id,
                appointment_id=event.appointment_id,
                clinic_id=event.clinic_id,
                from_status=event.from_status,
                to_status=event.to_status,
                event_type=event.event_type,
                title=event.title,
                notes=event.notes,
                actor_id=event.actor_id,
                actor_name=getattr(event, "actor_name", None),
                created_at=getattr(event, "created_at", None) or datetime.now(UTC),
            )
            for event in (apt.timeline_events or [])
        ]

        return AppointmentDetail(
            **read_model.model_dump(),
            patient_photo_url=patient_photo_url,
            patient_medical_alerts=medical_alerts,
            timeline_events=timeline_events,
        )

    async def count_today_appointments(self, clinic_id: UUID, target_date: date) -> int:
        query = select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.date == target_date,
        )
        return (await self.db.scalar(query)) or 0

    async def check_conflicts(
        self,
        clinic_id: UUID,
        dentist_id: UUID,
        chair_id: UUID,
        patient_id: UUID,
        target_date: date,
        start_time: time,
        end_time: time,
        exclude_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Detect dentist, chair, patient overlaps and blocked times."""
        active_statuses = [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_TREATMENT,
        ]

        # 1. Dentist conflict
        dentist_query = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.dentist_id == dentist_id,
            Appointment.date == target_date,
            Appointment.status.in_(active_statuses),
            Appointment.deleted_at.is_(None),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        if exclude_id:
            dentist_query = dentist_query.where(Appointment.id != exclude_id)
        dentist_conflict = await self.db.scalar(dentist_query)

        # 2. Chair conflict
        chair_query = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.chair_id == chair_id,
            Appointment.date == target_date,
            Appointment.status.in_(active_statuses),
            Appointment.deleted_at.is_(None),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        if exclude_id:
            chair_query = chair_query.where(Appointment.id != exclude_id)
        chair_conflict = await self.db.scalar(chair_query)

        # 3. Patient conflict
        patient_query = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.patient_id == patient_id,
            Appointment.date == target_date,
            Appointment.status.in_(active_statuses),
            Appointment.deleted_at.is_(None),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        if exclude_id:
            patient_query = patient_query.where(Appointment.id != exclude_id)
        patient_conflict = await self.db.scalar(patient_query)

        # 4. Dentist blocked time conflict
        # Combine target_date and times
        start_dt = datetime.combine(target_date, start_time)
        end_dt = datetime.combine(target_date, end_time)
        blocked_query = select(DentistBlockedTime).where(
            DentistBlockedTime.clinic_id == clinic_id,
            or_(
                DentistBlockedTime.dentist_id == dentist_id,
                DentistBlockedTime.dentist_id.is_(None),
            ),
            DentistBlockedTime.deleted_at.is_(None),
            DentistBlockedTime.start_time < end_dt,
            DentistBlockedTime.end_time > start_dt,
        )
        blocked_conflict = await self.db.scalar(blocked_query)

        return {
            "dentist_conflict": dentist_conflict,
            "chair_conflict": chair_conflict,
            "patient_conflict": patient_conflict,
            "blocked_conflict": blocked_conflict,
        }

    async def create(
        self,
        clinic_id: UUID,
        appointment_number: str,
        payload: AppointmentCreate,
        end_time: time,
        actor_id: UUID | None = None,
    ) -> Appointment:
        appointment = Appointment(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            dentist_id=payload.dentist_id,
            chair_id=payload.chair_id,
            appointment_number=appointment_number,
            date=payload.date,
            start_time=payload.start_time,
            end_time=end_time,
            duration=payload.duration,
            status=AppointmentStatus.SCHEDULED,
            visit_type=payload.visit_type,
            chief_complaint=payload.chief_complaint,
            priority=payload.priority,
            notes=payload.notes,
            is_emergency_override=payload.is_emergency_override,
            created_by=actor_id,
        )
        self.db.add(appointment)
        await self.db.flush()

        # Add initial timeline event
        timeline_event = AppointmentTimelineEvent(
            id=uuid4(),
            appointment_id=appointment.id,
            clinic_id=clinic_id,
            from_status=None,
            to_status=AppointmentStatus.SCHEDULED,
            event_type="CREATED",
            title="Appointment Created",
            notes=f"Scheduled for {payload.date} at {payload.start_time.strftime('%H:%M')}",
            actor_id=actor_id,
        )
        self.db.add(timeline_event)
        await self.db.flush()

        fetched = await self.get(clinic_id, appointment.id)
        return fetched or appointment

    async def get(self, clinic_id: UUID, appointment_id: UUID) -> Appointment | None:
        query = self._base_query(clinic_id).where(Appointment.id == appointment_id)
        return await self.db.scalar(query)

    async def update(
        self,
        appointment: Appointment,
        payload: AppointmentUpdate,
        end_time: time | None = None,
        actor_id: UUID | None = None,
    ) -> Appointment:
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(appointment, field, value)
        if end_time is not None:
            appointment.end_time = end_time

        timeline_event = AppointmentTimelineEvent(
            id=uuid4(),
            appointment_id=appointment.id,
            clinic_id=appointment.clinic_id,
            from_status=appointment.status,
            to_status=appointment.status,
            event_type="UPDATED",
            title="Appointment Details Updated",
            notes="Updated scheduling parameters or clinical notes",
            actor_id=actor_id,
        )
        self.db.add(timeline_event)
        await self.db.flush()
        fetched = await self.get(appointment.clinic_id, appointment.id)
        return fetched or appointment

    async def change_status(
        self,
        appointment: Appointment,
        new_status: AppointmentStatus,
        event_type: str,
        title: str,
        notes: str | None = None,
        cancellation_reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> Appointment:
        from_status = appointment.status
        appointment.status = new_status
        if cancellation_reason:
            appointment.cancellation_reason = cancellation_reason

        timeline_event = AppointmentTimelineEvent(
            id=uuid4(),
            appointment_id=appointment.id,
            clinic_id=appointment.clinic_id,
            from_status=from_status,
            to_status=new_status,
            event_type=event_type,
            title=title,
            notes=notes or cancellation_reason,
            actor_id=actor_id,
        )
        self.db.add(timeline_event)
        await self.db.flush()
        fetched = await self.get(appointment.clinic_id, appointment.id)
        return fetched or appointment

    async def reschedule(
        self,
        appointment: Appointment,
        new_date: date,
        new_start_time: time,
        new_end_time: time,
        duration: int,
        new_chair_id: UUID | None,
        new_dentist_id: UUID | None,
        reason: str,
        is_emergency_override: bool = False,
        actor_id: UUID | None = None,
    ) -> Appointment:
        old_date = appointment.date
        old_time = appointment.start_time

        appointment.date = new_date
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.duration = duration
        if new_chair_id:
            appointment.chair_id = new_chair_id
        if new_dentist_id:
            appointment.dentist_id = new_dentist_id
        appointment.is_emergency_override = is_emergency_override
        appointment.status = AppointmentStatus.RESCHEDULED

        timeline_event = AppointmentTimelineEvent(
            id=uuid4(),
            appointment_id=appointment.id,
            clinic_id=appointment.clinic_id,
            from_status=appointment.status,
            to_status=AppointmentStatus.RESCHEDULED,
            event_type="RESCHEDULED",
            title="Appointment Rescheduled",
            notes=f"Moved from {old_date} {old_time.strftime('%H:%M')} to {new_date} {new_start_time.strftime('%H:%M')}. Reason: {reason}",
            actor_id=actor_id,
        )
        self.db.add(timeline_event)
        await self.db.flush()
        fetched = await self.get(appointment.clinic_id, appointment.id)
        return fetched or appointment

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
    ) -> list[Appointment]:
        query = self._base_query(clinic_id)
        if patient_id and isinstance(patient_id, UUID):
            query = query.where(Appointment.patient_id == patient_id)
        if dentist_id and isinstance(dentist_id, UUID):
            query = query.where(Appointment.dentist_id == dentist_id)
        if chair_id and isinstance(chair_id, UUID):
            query = query.where(Appointment.chair_id == chair_id)
        if target_date and isinstance(target_date, date):
            query = query.where(Appointment.date == target_date)
        if start_date and isinstance(start_date, date):
            query = query.where(Appointment.date >= start_date)
        if end_date and isinstance(end_date, date):
            query = query.where(Appointment.date <= end_date)
        if status and isinstance(status, AppointmentStatus):
            query = query.where(Appointment.status == status)
        if visit_type and isinstance(visit_type, VisitType):
            query = query.where(Appointment.visit_type == visit_type)

        if search and isinstance(search, str) and search.strip():
            search_pattern = f"%{search.strip()}%"
            query = query.join(Appointment.patient).where(
                or_(
                    Appointment.appointment_number.ilike(search_pattern),
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    Patient.patient_number.ilike(search_pattern),
                    Patient.mobile_number.ilike(search_pattern),
                )
            )

        is_asc = sort_asc if isinstance(sort_asc, bool) else True
        if is_asc:
            query = query.order_by(Appointment.date.asc(), Appointment.start_time.asc())
        else:
            query = query.order_by(Appointment.date.desc(), Appointment.start_time.desc())

        offset_val = skip if isinstance(skip, int) and skip >= 0 else 0
        limit_val = limit if isinstance(limit, int) and limit > 0 else 50
        query = query.offset(offset_val).limit(limit_val)
        return list((await self.db.scalars(query)).all())

    async def get_day_calendar(self, clinic_id: UUID, target_date: date) -> list[Appointment]:
        query = (
            self._base_query(clinic_id)
            .where(
                Appointment.date == target_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.start_time.asc())
        )
        return list((await self.db.scalars(query)).all())

    async def get_week_calendar(
        self, clinic_id: UUID, start_date: date, end_date: date
    ) -> list[Appointment]:
        query = (
            self._base_query(clinic_id)
            .where(
                Appointment.date >= start_date,
                Appointment.date <= end_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
        )
        return list((await self.db.scalars(query)).all())

    async def get_month_calendar(
        self, clinic_id: UUID, year: int, month: int
    ) -> list[Appointment]:
        # Simple start and end of month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        query = (
            self._base_query(clinic_id)
            .where(
                Appointment.date >= start_date,
                Appointment.date <= end_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
        )
        return list((await self.db.scalars(query)).all())

    async def get_reception_queue(
        self, clinic_id: UUID, target_date: date
    ) -> list[AppointmentQueueItem]:
        query = (
            self._base_query(clinic_id)
            .where(
                Appointment.date == target_date,
                Appointment.status.in_(
                    [
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED,
                        AppointmentStatus.CHECKED_IN,
                        AppointmentStatus.IN_TREATMENT,
                        AppointmentStatus.COMPLETED,
                    ]
                ),
            )
            .order_by(Appointment.start_time.asc())
        )
        results = list((await self.db.scalars(query)).all())
        now = datetime.now(UTC)

        queue_items: list[AppointmentQueueItem] = []
        for apt in results:
            patient_name = "Patient"
            patient_number = "N/A"
            patient_phone = None
            if apt.patient:
                patient_name = f"{apt.patient.first_name} {apt.patient.last_name}"
                patient_number = apt.patient.patient_number
                patient_phone = apt.patient.mobile_number

            dentist_name = f"Dr. {apt.dentist.first_name} {apt.dentist.last_name}" if apt.dentist else "Dentist"
            chair_name = apt.chair.name if apt.chair else "Chair"

            # Compute checked_in_at or wait time
            checked_in_at = None
            treatment_started_at = None
            for event in apt.timeline_events:
                if event.event_type == "CHECKED_IN" and checked_in_at is None:
                    checked_in_at = event.created_at
                elif event.event_type == "TREATMENT_STARTED" and treatment_started_at is None:
                    treatment_started_at = event.created_at

            wait_minutes = None
            if checked_in_at and apt.status == AppointmentStatus.CHECKED_IN:
                # Naive diff
                naive_checkin = checked_in_at.replace(tzinfo=None)
                wait_minutes = max(0, int((now - naive_checkin).total_seconds() / 60))

            queue_items.append(
                AppointmentQueueItem(
                    id=apt.id,
                    appointment_number=apt.appointment_number,
                    patient_id=apt.patient_id,
                    patient_name=patient_name,
                    patient_number=patient_number,
                    patient_phone=patient_phone,
                    dentist_id=apt.dentist_id,
                    dentist_name=dentist_name,
                    chair_id=apt.chair_id,
                    chair_name=chair_name,
                    scheduled_time=apt.start_time,
                    duration=apt.duration,
                    status=getattr(apt, "status", None) or AppointmentStatus.SCHEDULED,
                    visit_type=getattr(apt, "visit_type", None) or VisitType.CONSULTATION,
                    priority=getattr(apt, "priority", None) or "NORMAL",
                    checked_in_at=checked_in_at,
                    treatment_started_at=treatment_started_at,
                    wait_minutes=wait_minutes,
                )
            )
        return queue_items

    async def get_dashboard_stats(
        self, clinic_id: UUID, target_date: date
    ) -> DashboardStatsResponse:
        query = select(Appointment.status, func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.date == target_date,
            Appointment.deleted_at.is_(None),
        ).group_by(Appointment.status)

        status_counts = dict((await self.db.execute(query)).all())

        total = sum(status_counts.values())
        completed = status_counts.get(AppointmentStatus.COMPLETED, 0)
        cancelled = status_counts.get(AppointmentStatus.CANCELLED, 0)
        no_show = status_counts.get(AppointmentStatus.NO_SHOW, 0)
        waiting = status_counts.get(AppointmentStatus.CHECKED_IN, 0)
        in_treatment = status_counts.get(AppointmentStatus.IN_TREATMENT, 0)

        # Count follow-up visits scheduled within next 7 days
        follow_ups_query = select(func.count(Appointment.id)).where(
            Appointment.clinic_id == clinic_id,
            Appointment.date > target_date,
            Appointment.deleted_at.is_(None),
        )
        raw_fu = await self.db.scalar(follow_ups_query)
        upcoming_follow_ups = int(raw_fu) if isinstance(raw_fu, (int, float)) else 0

        # Placeholder revenue: e.g. completed * 1500 INR + in_treatment * 1200 INR
        revenue_placeholder = float((completed * 1500) + (in_treatment * 1000))

        return DashboardStatsResponse(
            date=target_date,
            total_appointments=total,
            completed=completed,
            cancelled=cancelled,
            no_show=no_show,
            waiting=waiting,
            in_treatment=in_treatment,
            upcoming_follow_ups=upcoming_follow_ups,
            revenue_placeholder=revenue_placeholder,
        )

    async def get_dentist_schedule(
        self, clinic_id: UUID, dentist_id: UUID, start_date: date, end_date: date
    ) -> DentistScheduleRead:
        dentist = await self.db.get(User, dentist_id)
        dentist_name = f"Dr. {dentist.first_name} {dentist.last_name}" if dentist else "Dentist"

        # Working hours
        wh_query = select(DentistWorkingHour).where(
            DentistWorkingHour.clinic_id == clinic_id,
            DentistWorkingHour.dentist_id == dentist_id,
            DentistWorkingHour.is_active.is_(True),
            DentistWorkingHour.deleted_at.is_(None),
        ).order_by(DentistWorkingHour.day_of_week.asc())
        working_hours = [
            WorkingHourRead.model_validate(wh)
            for wh in (await self.db.scalars(wh_query)).all()
            if isinstance(wh, DentistWorkingHour)
        ]

        # Blocked times
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        bt_query = select(DentistBlockedTime).where(
            DentistBlockedTime.clinic_id == clinic_id,
            or_(
                DentistBlockedTime.dentist_id == dentist_id,
                DentistBlockedTime.dentist_id.is_(None),
            ),
            DentistBlockedTime.deleted_at.is_(None),
            DentistBlockedTime.start_time <= end_dt,
            DentistBlockedTime.end_time >= start_dt,
        )
        blocked_times = [
            BlockedTimeRead.model_validate(bt)
            for bt in (await self.db.scalars(bt_query)).all()
            if isinstance(bt, DentistBlockedTime)
        ]

        # Appointments
        apt_query = (
            self._base_query(clinic_id)
            .where(
                Appointment.dentist_id == dentist_id,
                Appointment.date >= start_date,
                Appointment.date <= end_date,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
        )
        appointments = [
            self.to_read_model(apt)
            for apt in (await self.db.scalars(apt_query)).all()
            if isinstance(apt, Appointment)
        ]

        return DentistScheduleRead(
            dentist_id=dentist_id,
            dentist_name=dentist_name,
            working_hours=working_hours,
            blocked_times=blocked_times,
            appointments=appointments,
        )
