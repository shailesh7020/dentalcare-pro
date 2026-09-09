# backend/app/services/remote_notification_service.py
"""
DentalCare Pro - Remote Notification Service
Handles appointment reminders, low stock alerts, backup warnings,
and revenue reports via database logs, Web Push, and email.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    DeliveryChannel,
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)

logger = logging.getLogger("dentalcare.remote_notifications")


class RemoteNotificationService:
    @classmethod
    async def create_and_dispatch(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        recipient_user_id: UUID | None = None,
        recipient_email: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        """Record notification in database and format multi-channel dispatch."""
        notif = Notification(
            clinic_id=clinic_id,
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            priority=priority,
            delivery_channel=DeliveryChannel.IN_APP,
            title=title,
            message=body,
            status=NotificationStatus.SENT,
            data_json=json.dumps(metadata or {}),
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

        logger.info(
            "Remote notification created: clinic=%s, title='%s', priority=%s",
            clinic_id,
            title,
            priority.value,
        )
        return notif

    @classmethod
    async def notify_appointment_reminder(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        patient_name: str,
        appointment_time: str,
        dentist_name: str,
        doctor_user_id: UUID | None = None,
    ) -> Notification:
        """Send appointment alert for upcoming clinical visit."""
        title = f"Upcoming Visit: {patient_name}"
        body = f"Appointment scheduled at {appointment_time} with {dentist_name}."
        return await cls.create_and_dispatch(
            db=db,
            clinic_id=clinic_id,
            title=title,
            body=body,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            priority=NotificationPriority.NORMAL,
            recipient_user_id=doctor_user_id,
            metadata={"patient_name": patient_name, "time": appointment_time},
        )

    @classmethod
    async def notify_low_stock(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        item_name: str,
        current_stock: int,
        minimum_stock: int,
    ) -> Notification:
        """Send critical inventory depletion warning."""
        title = f"Low Stock Warning: {item_name}"
        body = f"Inventory level reached {current_stock} (Minimum: {minimum_stock}). Restock recommended."
        return await cls.create_and_dispatch(
            db=db,
            clinic_id=clinic_id,
            title=title,
            body=body,
            notification_type=NotificationType.LOW_INVENTORY,
            priority=NotificationPriority.HIGH,
            metadata={"item_name": item_name, "current": current_stock, "minimum": minimum_stock},
        )

    @classmethod
    async def notify_backup_status(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        file_name: str,
        is_success: bool,
        error_message: str | None = None,
    ) -> Notification:
        """Send backup execution status."""
        if is_success:
            title = "Database Backup Succeeded"
            body = f"Encrypted backup {file_name} created and verified successfully."
            priority = NotificationPriority.LOW
        else:
            title = "CRITICAL: Database Backup Failed"
            body = f"Backup failed: {error_message or 'Unknown error'}. Immediate attention required."
            priority = NotificationPriority.URGENT

        return await cls.create_and_dispatch(
            db=db,
            clinic_id=clinic_id,
            title=title,
            body=body,
            notification_type=NotificationType.SYSTEM_ALERT,
            priority=priority,
            metadata={"backup_file": file_name, "success": is_success},
        )

    @classmethod
    def format_web_push_payload(cls, notif: Any) -> dict[str, Any]:
        """Format Web Push API standard payload for browser push notifications."""
        notif_type = getattr(notif, "notification_type", getattr(notif, "type", "SYSTEM_ALERT"))
        type_val = getattr(notif_type, "value", str(notif_type))
        body_val = getattr(notif, "message", getattr(notif, "body", ""))
        return {
            "notification": {
                "title": notif.title,
                "body": body_val,
                "icon": "/icons/icon-192x192.png",
                "badge": "/icons/badge-72x72.png",
                "data": {
                    "notification_id": str(notif.id),
                    "type": type_val,
                    "url": "/mobile",
                },
                "actions": [
                    {"action": "open", "title": "Open Mobile App"},
                    {"action": "dismiss", "title": "Dismiss"},
                ],
            }
        }
