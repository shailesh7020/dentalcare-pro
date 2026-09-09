import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.models.appointment import Appointment

logger = logging.getLogger(__name__)


class NotificationType(StrEnum):
    CONFIRMATION = "CONFIRMATION"
    REMINDER = "REMINDER"
    CANCELLATION = "CANCELLATION"
    RESCHEDULE = "RESCHEDULE"
    FOLLOW_UP = "FOLLOW_UP"


class NotificationChannel(StrEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"


@dataclass
class NotificationIntent:
    notification_type: NotificationType
    clinic_id: UUID
    patient_id: UUID
    appointment_id: UUID
    channels: list[NotificationChannel]
    recipient_phone: str | None
    recipient_email: str | None
    subject: str
    message: str
    metadata: dict[str, Any]
    created_at: datetime


class NotificationService:
    """Pluggable notification dispatcher preparing infrastructure for SMS/Email/WhatsApp."""

    def __init__(self):
        self._intents: list[NotificationIntent] = []

    def dispatch_appointment_event(
        self,
        notification_type: NotificationType,
        appointment: Appointment,
        extra_note: str | None = None,
    ) -> NotificationIntent:
        recipient_phone = appointment.patient.mobile_number if appointment.patient else None
        recipient_email = appointment.patient.email if appointment.patient else None
        patient_name = (
            f"{appointment.patient.first_name} {appointment.patient.last_name}"
            if appointment.patient
            else "Patient"
        )
        date_str = appointment.date.strftime("%d %b %Y")
        time_str = appointment.start_time.strftime("%I:%M %p")

        subjects = {
            NotificationType.CONFIRMATION: f"Appointment Confirmed: {date_str} at {time_str}",
            NotificationType.REMINDER: f"Reminder: Dental Appointment on {date_str} at {time_str}",
            NotificationType.CANCELLATION: f"Appointment Cancelled: {date_str}",
            NotificationType.RESCHEDULE: f"Appointment Rescheduled to {date_str} at {time_str}",
            NotificationType.FOLLOW_UP: "Follow-up Dental Care Check-in",
        }

        messages = {
            NotificationType.CONFIRMATION: (
                f"Dear {patient_name}, your dental appointment #{appointment.appointment_number} "
                f"is confirmed for {date_str} at {time_str}."
            ),
            NotificationType.REMINDER: (
                f"Dear {patient_name}, this is a reminder for your upcoming appointment on {date_str} at {time_str}."
            ),
            NotificationType.CANCELLATION: (
                f"Dear {patient_name}, your appointment on {date_str} has been cancelled. "
                f"Reason: {extra_note or 'As requested.'}"
            ),
            NotificationType.RESCHEDULE: (
                f"Dear {patient_name}, your appointment has been rescheduled to {date_str} at {time_str}. "
                f"Note: {extra_note or 'None.'}"
            ),
            NotificationType.FOLLOW_UP: (
                f"Dear {patient_name}, we hope you are recovering well from your visit. "
                f"Please contact us if you experience any discomfort."
            ),
        }

        intent = NotificationIntent(
            notification_type=notification_type,
            clinic_id=appointment.clinic_id,
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            channels=[NotificationChannel.SMS, NotificationChannel.WHATSAPP],
            recipient_phone=recipient_phone,
            recipient_email=recipient_email,
            subject=subjects.get(notification_type, "DentalCare Pro Notification"),
            message=messages.get(notification_type, ""),
            metadata={
                "appointment_number": appointment.appointment_number,
                "visit_type": str(appointment.visit_type),
                "chair_id": str(appointment.chair_id),
                "dentist_id": str(appointment.dentist_id),
            },
            created_at=datetime.now(UTC),
        )

        self._intents.append(intent)
        logger.info(
            "Dispatched notification intent [%s] for appointment %s to %s",
            notification_type,
            appointment.appointment_number,
            recipient_phone or recipient_email,
        )
        return intent

    def get_dispatched_intents(self) -> list[NotificationIntent]:
        return list(self._intents)


# Singleton instance
notification_service = NotificationService()
