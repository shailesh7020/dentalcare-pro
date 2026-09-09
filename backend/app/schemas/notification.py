from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import (
    DeliveryChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


class NotificationBase(BaseModel):
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    delivery_channel: DeliveryChannel = DeliveryChannel.IN_APP
    title: str = Field(..., max_length=255)
    message: str
    data_json: str | None = None


class NotificationCreate(NotificationBase):
    recipient_user_id: UUID | None = None
    patient_id: UUID | None = None


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    recipient_user_id: UUID | None = None
    patient_id: UUID | None = None
    status: NotificationStatus
    is_read: bool = False
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime


class NotificationUpdateStatus(BaseModel):
    status: NotificationStatus


class NotificationTemplateBase(BaseModel):
    template_code: str = Field(..., max_length=80)
    channel: DeliveryChannel = DeliveryChannel.EMAIL
    subject_template: str = Field(..., max_length=255)
    body_template: str
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    subject_template: str | None = None
    body_template: str | None = None
    channel: DeliveryChannel | None = None
    is_active: bool | None = None


class NotificationTemplateRead(NotificationTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID | None = None
    created_at: datetime


class ClinicNotificationSettingBase(BaseModel):
    enable_email: bool = True
    enable_sms: bool = True
    enable_whatsapp: bool = False
    reminder_intervals_hours: str = "168,72,24,2"
    sender_email: str | None = None
    sender_phone: str | None = None


class ClinicNotificationSettingUpdate(BaseModel):
    enable_email: bool | None = None
    enable_sms: bool | None = None
    enable_whatsapp: bool | None = None
    reminder_intervals_hours: str | None = None
    sender_email: str | None = None
    sender_phone: str | None = None


class ClinicNotificationSettingRead(ClinicNotificationSettingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_at: datetime


class NotificationBulkCreate(BaseModel):
    notifications: list[NotificationCreate]


class NotificationStats(BaseModel):
    total_count: int
    unread_count: int
    pending_dispatch: int
    by_priority: dict[str, int]
    by_channel: dict[str, int]


class NotificationStatsRead(NotificationStats):
    pass


class ReminderProcessResult(BaseModel):
    scanned_appointments: int
    reminders_created: int
    reminders_dispatched: int


class FollowUpProcessResult(BaseModel):
    scanned_followups: int
    reminders_created: int

