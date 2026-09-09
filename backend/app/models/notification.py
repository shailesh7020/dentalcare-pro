from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import Clinic, User
    from app.models.patient import Patient


class NotificationType(StrEnum):
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"
    FOLLOW_UP_REMINDER = "FOLLOW_UP_REMINDER"
    PRESCRIPTION_READY = "PRESCRIPTION_READY"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    LOW_INVENTORY = "LOW_INVENTORY"
    NEW_TASK_ASSIGNED = "NEW_TASK_ASSIGNED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class NotificationPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"


class DeliveryChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"


class Notification(Base, UUIDAuditMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_clinic_id", "clinic_id"),
        Index("ix_notifications_recipient_user_id", "recipient_user_id"),
        Index("ix_notifications_patient_id", "patient_id"),
        Index("ix_notifications_status", "clinic_id", "status"),
        Index("ix_notifications_type", "clinic_id", "notification_type"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority"),
        default=NotificationPriority.NORMAL,
        nullable=False,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"),
        default=NotificationStatus.PENDING,
        nullable=False,
    )
    delivery_channel: Mapped[DeliveryChannel] = mapped_column(
        Enum(DeliveryChannel, name="delivery_channel"),
        default=DeliveryChannel.IN_APP,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data_json: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    clinic: Mapped[Clinic] = relationship("Clinic")
    recipient_user: Mapped[User | None] = relationship("User", foreign_keys=[recipient_user_id])
    patient: Mapped[Patient | None] = relationship("Patient", foreign_keys=[patient_id])

    @property
    def is_read(self) -> bool:
        return self.read_at is not None or self.status == NotificationStatus.READ



class NotificationTemplate(Base, UUIDAuditMixin):
    __tablename__ = "notification_templates"
    __table_args__ = (
        Index("ix_notification_templates_clinic_id", "clinic_id"),
        Index("ix_notification_templates_code", "template_code"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
    )
    template_code: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[DeliveryChannel] = mapped_column(
        Enum(DeliveryChannel, name="notification_template_channel"),
        default=DeliveryChannel.EMAIL,
        nullable=False,
    )
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic | None] = relationship("Clinic")


class ClinicNotificationSetting(Base, UUIDAuditMixin):
    __tablename__ = "clinic_notification_settings"
    __table_args__ = (
        UniqueConstraint("clinic_id", name="uq_clinic_notification_setting"),
        Index("ix_clinic_notification_settings_clinic_id", "clinic_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    enable_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_sms: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_intervals_hours: Mapped[str] = mapped_column(
        String(100), default="168,72,24,2", nullable=False
    )
    sender_email: Mapped[str | None] = mapped_column(String(120))
    sender_phone: Mapped[str | None] = mapped_column(String(40))

    clinic: Mapped[Clinic] = relationship("Clinic")
