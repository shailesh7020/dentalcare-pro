from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.identity import Clinic
from app.models.notification import (
    DeliveryChannel,
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.schemas.notification import NotificationCreate, ReminderProcessResult
from app.services.notifications.notification_service import NotificationService


class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notif_service = NotificationService(db)

    async def process_appointment_reminders(self, clinic_id: UUID) -> ReminderProcessResult:
        """
        Scans upcoming appointments across configured reminder windows:
        e.g., 7 days (168h), 3 days (72h), 24 hours (24h), 2 hours (2h).
        Guarantees idempotency by checking existing reminders sent for that interval.
        """
        settings = await self.notif_service.get_settings(clinic_id)
        raw_intervals = [
            int(h.strip())
            for h in settings.reminder_intervals_hours.split(",")
            if h.strip().isdigit()
        ]
        intervals = sorted(raw_intervals, reverse=True)

        now = datetime.now(UTC)
        max_lookahead = timedelta(hours=max(intervals) + 1 if intervals else 168)
        max_date = (now + max_lookahead).date()

        # 1. Fetch active scheduled or confirmed appointments
        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.dentist),
            )
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                Appointment.date >= now.date(),
                Appointment.date <= max_date,
                Appointment.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        appointments = list(res.scalars().all())

        scanned = len(appointments)
        created = 0
        dispatched = 0

        clinic = await self.db.get(Clinic, clinic_id)
        clinic_name = clinic.name if clinic else "DentalCare Pro"
        clinic_phone = clinic.phone if clinic else "+91 99000 11223"

        for appt in appointments:
            if not appt.patient:
                continue

            # Compute approximate datetime of appointment
            appt_dt = datetime.combine(appt.date, appt.start_time, tzinfo=UTC)
            hours_until = (appt_dt - now).total_seconds() / 3600.0

            if hours_until <= 0:
                continue

            for target_hours in intervals:
                # Match window (within 1 hour tolerance of target)
                if abs(hours_until - target_hours) <= 1.5:
                    tag = f"reminder_{target_hours}h"

                    # Idempotency check: notification already created for this appointment + tag?
                    tag_check = (
                        select(Notification.id)
                        .where(
                            Notification.clinic_id == clinic_id,
                            Notification.patient_id == appt.patient_id,
                            Notification.notification_type == NotificationType.APPOINTMENT_REMINDER,
                            Notification.data_json.like(f"%{appt.id}%"),
                            Notification.data_json.like(f"%{tag}%"),
                        )
                        .limit(1)
                    )
                    existing = await self.db.scalar(tag_check)
                    if existing:
                        continue

                    # Context for template
                    ctx = {
                        "patient_name": f"{appt.patient.first_name} {appt.patient.last_name}",
                        "dentist_name": f"{appt.dentist.first_name} {appt.dentist.last_name}" if appt.dentist else "Dentist",
                        "appointment_date": appt.date.strftime("%d %b %Y"),
                        "appointment_time": appt.start_time.strftime("%I:%M %p"),
                        "clinic_name": clinic_name,
                        "clinic_phone": clinic_phone,
                    }

                    # Determine channels to dispatch
                    channels: list[DeliveryChannel] = [DeliveryChannel.IN_APP]
                    if settings.enable_sms and appt.patient.mobile_number:
                        channels.append(DeliveryChannel.SMS)
                    if settings.enable_email and appt.patient.email:
                        channels.append(DeliveryChannel.EMAIL)
                    if settings.enable_whatsapp and appt.patient.mobile_number:
                        channels.append(DeliveryChannel.WHATSAPP)

                    for ch in channels:
                        payload = NotificationCreate(
                            notification_type=NotificationType.APPOINTMENT_REMINDER,
                            priority=NotificationPriority.HIGH if target_hours <= 2 else NotificationPriority.NORMAL,
                            delivery_channel=ch,
                            patient_id=appt.patient_id,
                            title=f"Upcoming Visit Reminder: {clinic_name}",
                            message=f"Reminder for your visit on {appt.date.strftime('%d %b %Y')} at {appt.start_time.strftime('%I:%M %p')} with {ctx['dentist_name']}.",
                            data_json=json.dumps({"appointment_id": str(appt.id), "tag": tag, "hours": target_hours}),
                        )
                        await self.notif_service.send_notification(clinic_id, payload, context=ctx)
                        created += 1
                        dispatched += 1

        return ReminderProcessResult(
            scanned_appointments=scanned,
            reminders_created=created,
            reminders_dispatched=dispatched,
        )

    async def process_missed_appointment_followups(self, clinic_id: UUID) -> ReminderProcessResult:
        """Finds missed visits from the last 1-3 days and dispatches rescheduling follow-ups."""
        now = datetime.now(UTC)
        past_window_start = (now - timedelta(days=3)).date()
        past_window_end = (now - timedelta(days=1)).date()

        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.dentist),
            )
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.status.in_([AppointmentStatus.CANCELLED, AppointmentStatus.SCHEDULED]),
                Appointment.date >= past_window_start,
                Appointment.date <= past_window_end,
                Appointment.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        appointments = list(res.scalars().all())

        scanned = len(appointments)
        created = 0
        dispatched = 0

        clinic = await self.db.get(Clinic, clinic_id)
        clinic_name = clinic.name if clinic else "DentalCare Pro"
        clinic_phone = clinic.phone if clinic else "+91 99000 11223"

        for appt in appointments:
            if not appt.patient:
                continue

            tag = f"missed_followup_{appt.id}"
            tag_check = (
                select(Notification.id)
                .where(
                    Notification.clinic_id == clinic_id,
                    Notification.patient_id == appt.patient_id,
                    Notification.data_json.like(f"%{tag}%"),
                )
                .limit(1)
            )
            existing = await self.db.scalar(tag_check)
            if existing:
                continue

            ctx = {
                "patient_name": f"{appt.patient.first_name} {appt.patient.last_name}",
                "appointment_date": appt.date.strftime("%d %b %Y"),
                "clinic_name": clinic_name,
                "clinic_phone": clinic_phone,
            }

            payload = NotificationCreate(
                notification_type=NotificationType.APPOINTMENT_REMINDER,
                priority=NotificationPriority.NORMAL,
                delivery_channel=DeliveryChannel.IN_APP,
                patient_id=appt.patient_id,
                title=f"Missed Dental Visit Follow-up: {clinic_name}",
                message=f"We noticed you were unable to make your visit on {appt.date.strftime('%d %b %Y')}. Your oral health is important to us. Please call {clinic_phone} to reschedule.",
                data_json=json.dumps({"appointment_id": str(appt.id), "tag": tag}),
            )
            await self.notif_service.send_notification(clinic_id, payload, context=ctx)
            created += 1
            dispatched += 1

        return ReminderProcessResult(
            scanned_appointments=scanned,
            reminders_created=created,
            reminders_dispatched=dispatched,
        )

    async def scan_and_send_reminders(self, clinic_id: UUID) -> ReminderProcessResult:
        return await self.process_appointment_reminders(clinic_id)


AppointmentReminderService = ReminderService

