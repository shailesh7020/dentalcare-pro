from __future__ import annotations

import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Role, User
from app.models.notification import (
    DeliveryChannel,
    NotificationStatus,
    NotificationTemplate,
)
from app.models.patient import Patient
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    ClinicNotificationSettingRead,
    ClinicNotificationSettingUpdate,
    NotificationBulkCreate,
    NotificationCreate,
    NotificationRead,
    NotificationStats,
    NotificationTemplateCreate,
    NotificationTemplateRead,
    NotificationTemplateUpdate,
)
from app.services.notifications.providers.base import NotificationChannelProvider
from app.services.notifications.providers.email import EmailNotificationProvider
from app.services.notifications.providers.in_app import InAppNotificationProvider
from app.services.notifications.providers.sms import SmsNotificationProvider
from app.services.notifications.providers.whatsapp import WhatsAppNotificationProvider
from app.services.notifications.template_engine import DEFAULT_TEMPLATES, render_template


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)
        self.providers: dict[DeliveryChannel, NotificationChannelProvider] = {
            DeliveryChannel.IN_APP: InAppNotificationProvider(),
            DeliveryChannel.EMAIL: EmailNotificationProvider(),
            DeliveryChannel.SMS: SmsNotificationProvider(),
            DeliveryChannel.WHATSAPP: WhatsAppNotificationProvider(),
            DeliveryChannel.PUSH: InAppNotificationProvider(),
        }

    async def send_notification(
        self,
        clinic_id: UUID,
        payload: NotificationCreate,
        actor: User | None = None,
        context: dict | None = None,
    ) -> NotificationRead:
        # 1. Check template if title/message can be enriched
        type_str = payload.notification_type.value
        title = payload.title
        message = payload.message

        if context:
            tmpl = await self.repo.get_template(clinic_id, type_str, payload.delivery_channel)
            if tmpl:
                title = render_template(tmpl.subject_template, context)
                message = render_template(tmpl.body_template, context)
            elif type_str in DEFAULT_TEMPLATES:
                d = DEFAULT_TEMPLATES[type_str]
                title = render_template(d["subject"], context)
                message = render_template(d["body"], context)

        # 2. Persist notification
        create_data = payload.model_copy(update={"title": title, "message": message})
        notification = await self.repo.create_notification(
            clinic_id, create_data, actor_id=actor.id if actor else None
        )

        # 3. Resolve recipient destination string (email or phone)
        destination = "in_app"
        if payload.delivery_channel in (DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.WHATSAPP):
            if payload.patient_id:
                patient = await self.db.get(Patient, payload.patient_id)
                if patient:
                    if payload.delivery_channel == DeliveryChannel.EMAIL:
                        destination = patient.email or "no-email@patient.local"
                    else:
                        destination = patient.mobile_number
            elif payload.recipient_user_id:
                user = await self.db.get(User, payload.recipient_user_id)
                if user:
                    destination = user.email

        # 4. Dispatch via provider
        provider = self.providers.get(payload.delivery_channel)
        if provider:
            parsed_data = json.loads(payload.data_json) if payload.data_json else None
            result = await provider.send(
                recipient=destination,
                title=title,
                message=message,
                data=parsed_data,
            )
            if result.success:
                await self.repo.mark_delivered(notification)
            else:
                notification.status = NotificationStatus.FAILED

        await self.db.commit()
        return NotificationRead.model_validate(notification)

    async def list_notifications(
        self,
        clinic_id: UUID,
        recipient_user_id: UUID | None = None,
        patient_id: UUID | None = None,
        status: NotificationStatus | None = None,
        delivery_channel: DeliveryChannel | None = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[NotificationRead], int]:
        items, total = await self.repo.list_notifications(
            clinic_id=clinic_id,
            recipient_user_id=recipient_user_id,
            patient_id=patient_id,
            status=status,
            delivery_channel=delivery_channel,
            unread_only=unread_only,
            skip=skip,
            limit=limit,
        )
        return [NotificationRead.model_validate(i) for i in items], total

    async def mark_read(self, clinic_id: UUID, notification_id: UUID, actor: User) -> NotificationRead:
        notification = await self.repo.get_notification(clinic_id, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found.")

        # Authorization: patient can only read their own notifications
        if actor.role == Role.PATIENT and notification.patient_id != actor.patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to notification.")

        await self.repo.mark_read(notification)
        await self.db.commit()
        return NotificationRead.model_validate(notification)

    async def mark_notification_as_read(
        self, clinic_id: UUID, notification_id: UUID, actor: User | None = None
    ) -> NotificationRead:
        notification = await self.repo.get_notification(clinic_id, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found.")
        if actor and actor.role == Role.PATIENT and notification.patient_id != actor.patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to notification.")
        await self.repo.mark_read(notification)
        await self.db.commit()
        return NotificationRead.model_validate(notification)

    async def send_bulk_notifications(
        self, clinic_id: UUID, payload: NotificationBulkCreate, actor: User | None = None
    ) -> list[NotificationRead]:
        results = []
        for notif_create in payload.notifications:
            res = await self.send_notification(clinic_id, notif_create, actor=actor)
            results.append(res)
        return results


    async def mark_all_read(
        self, clinic_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> int:
        count = await self.repo.mark_all_read(clinic_id, user_id=user_id, patient_id=patient_id)
        await self.db.commit()
        return count

    async def get_stats(
        self, clinic_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> NotificationStats:
        data = await self.repo.get_stats(clinic_id, user_id=user_id, patient_id=patient_id)
        return NotificationStats(**data)

    # ----------------------------------------------------
    # Templates & Settings
    # ----------------------------------------------------
    async def list_templates(self, clinic_id: UUID) -> list[NotificationTemplateRead]:
        items = await self.repo.list_templates(clinic_id)
        return [NotificationTemplateRead.model_validate(i) for i in items]

    async def create_template(
        self, clinic_id: UUID, payload: NotificationTemplateCreate, actor: User
    ) -> NotificationTemplateRead:
        if actor.role not in (Role.SUPER_ADMIN, Role.CLINIC_ADMIN):
            raise HTTPException(status_code=403, detail="Only clinic admins can create templates.")
        item = await self.repo.create_template(clinic_id, payload, actor_id=actor.id)
        await self.db.commit()
        return NotificationTemplateRead.model_validate(item)

    async def update_template(
        self, clinic_id: UUID, template_id: UUID, payload: NotificationTemplateUpdate, actor: User
    ) -> NotificationTemplateRead:
        if actor.role not in (Role.SUPER_ADMIN, Role.CLINIC_ADMIN):
            raise HTTPException(status_code=403, detail="Only clinic admins can update templates.")
        item = await self.db.get(NotificationTemplate, template_id)
        if not item or (item.clinic_id and item.clinic_id != clinic_id):
            raise HTTPException(status_code=404, detail="Notification template not found.")
        updated = await self.repo.update_template(item, payload, actor_id=actor.id)
        await self.db.commit()
        return NotificationTemplateRead.model_validate(updated)

    async def get_settings(self, clinic_id: UUID) -> ClinicNotificationSettingRead:
        setting = await self.repo.get_or_create_settings(clinic_id)
        return ClinicNotificationSettingRead.model_validate(setting)

    async def update_settings(
        self, clinic_id: UUID, payload: ClinicNotificationSettingUpdate, actor: User
    ) -> ClinicNotificationSettingRead:
        if actor.role not in (Role.SUPER_ADMIN, Role.CLINIC_ADMIN):
            raise HTTPException(status_code=403, detail="Only clinic admins can modify settings.")
        setting = await self.repo.get_or_create_settings(clinic_id)
        updated = await self.repo.update_settings(setting, payload, actor_id=actor.id)
        await self.db.commit()
        return ClinicNotificationSettingRead.model_validate(updated)
