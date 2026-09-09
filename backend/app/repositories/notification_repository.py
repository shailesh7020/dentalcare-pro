from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    ClinicNotificationSetting,
    DeliveryChannel,
    Notification,
    NotificationStatus,
    NotificationTemplate,
)
from app.schemas.notification import (
    ClinicNotificationSettingUpdate,
    NotificationCreate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
)


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------
    # Notifications
    # ----------------------------------------------------
    async def create_notification(
        self, clinic_id: UUID, payload: NotificationCreate, actor_id: UUID | None = None
    ) -> Notification:
        notification = Notification(
            id=uuid4(),
            clinic_id=clinic_id,
            recipient_user_id=payload.recipient_user_id,
            patient_id=payload.patient_id,
            notification_type=payload.notification_type,
            priority=payload.priority,
            status=NotificationStatus.PENDING,
            delivery_channel=payload.delivery_channel,
            title=payload.title,
            message=payload.message,
            data_json=payload.data_json,
            created_by=actor_id,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_notification(self, clinic_id: UUID, notification_id: UUID) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.clinic_id == clinic_id,
            Notification.deleted_at.is_(None),
        )
        return await self.db.scalar(stmt)

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
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(
            Notification.clinic_id == clinic_id,
            Notification.deleted_at.is_(None),
        )

        if recipient_user_id:
            stmt = stmt.where(Notification.recipient_user_id == recipient_user_id)
        if patient_id:
            stmt = stmt.where(Notification.patient_id == patient_id)
        if status:
            stmt = stmt.where(Notification.status == status)
        if delivery_channel:
            stmt = stmt.where(Notification.delivery_channel == delivery_channel)
        if unread_only:
            stmt = stmt.where(Notification.status != NotificationStatus.READ)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def mark_delivered(self, notification: Notification) -> Notification:
        notification.status = NotificationStatus.DELIVERED
        notification.delivered_at = datetime.now(UTC)
        await self.db.flush()
        return notification

    async def mark_read(self, notification: Notification) -> Notification:
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now(UTC)
        await self.db.flush()
        return notification

    async def mark_all_read(
        self, clinic_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.clinic_id == clinic_id,
                Notification.status != NotificationStatus.READ,
                Notification.deleted_at.is_(None),
            )
            .values(
                status=NotificationStatus.READ,
                read_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        if user_id:
            stmt = stmt.where(Notification.recipient_user_id == user_id)
        if patient_id:
            stmt = stmt.where(Notification.patient_id == patient_id)

        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount

    async def get_stats(
        self, clinic_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> dict:
        base_where = [Notification.clinic_id == clinic_id, Notification.deleted_at.is_(None)]
        if user_id:
            base_where.append(Notification.recipient_user_id == user_id)
        if patient_id:
            base_where.append(Notification.patient_id == patient_id)

        # total
        total_stmt = select(func.count(Notification.id)).where(*base_where)
        total = await self.db.scalar(total_stmt) or 0

        # unread
        unread_stmt = select(func.count(Notification.id)).where(
            *base_where, Notification.status != NotificationStatus.READ
        )
        unread = await self.db.scalar(unread_stmt) or 0

        # pending
        pending_stmt = select(func.count(Notification.id)).where(
            *base_where, Notification.status == NotificationStatus.PENDING
        )
        pending = await self.db.scalar(pending_stmt) or 0

        # priority breakdown
        p_stmt = (
            select(Notification.priority, func.count(Notification.id))
            .where(*base_where)
            .group_by(Notification.priority)
        )
        p_res = await self.db.execute(p_stmt)
        by_priority = {str(row[0].value): int(row[1]) for row in p_res.all()}

        # channel breakdown
        c_stmt = (
            select(Notification.delivery_channel, func.count(Notification.id))
            .where(*base_where)
            .group_by(Notification.delivery_channel)
        )
        c_res = await self.db.execute(c_stmt)
        by_channel = {str(row[0].value): int(row[1]) for row in c_res.all()}

        return {
            "total_count": total,
            "unread_count": unread,
            "pending_dispatch": pending,
            "by_priority": by_priority,
            "by_channel": by_channel,
        }

    async def get_notification_stats(
        self, clinic_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> dict:
        return await self.get_stats(clinic_id, user_id=user_id, patient_id=patient_id)


    # ----------------------------------------------------
    # Templates
    # ----------------------------------------------------
    async def get_template(
        self, clinic_id: UUID | None, template_code: str, channel: DeliveryChannel
    ) -> NotificationTemplate | None:
        stmt = (
            select(NotificationTemplate)
            .where(
                NotificationTemplate.template_code == template_code,
                NotificationTemplate.channel == channel,
                NotificationTemplate.is_active.is_(True),
                NotificationTemplate.deleted_at.is_(None),
            )
            .order_by(NotificationTemplate.clinic_id.desc().nullslast())
        )
        if clinic_id:
            stmt = stmt.where((NotificationTemplate.clinic_id == clinic_id) | (NotificationTemplate.clinic_id.is_(None)))
        else:
            stmt = stmt.where(NotificationTemplate.clinic_id.is_(None))

        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_templates(self, clinic_id: UUID) -> list[NotificationTemplate]:
        stmt = (
            select(NotificationTemplate)
            .where(
                (NotificationTemplate.clinic_id == clinic_id) | (NotificationTemplate.clinic_id.is_(None)),
                NotificationTemplate.deleted_at.is_(None),
            )
            .order_by(NotificationTemplate.template_code)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_template(
        self, clinic_id: UUID, payload: NotificationTemplateCreate, actor_id: UUID | None = None
    ) -> NotificationTemplate:
        template = NotificationTemplate(
            id=uuid4(),
            clinic_id=clinic_id,
            template_code=payload.template_code,
            channel=payload.channel,
            subject_template=payload.subject_template,
            body_template=payload.body_template,
            is_active=payload.is_active,
            created_by=actor_id,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def update_template(
        self, template: NotificationTemplate, payload: NotificationTemplateUpdate, actor_id: UUID | None = None
    ) -> NotificationTemplate:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        template.updated_by = actor_id
        await self.db.flush()
        return template

    # ----------------------------------------------------
    # Settings
    # ----------------------------------------------------
    async def get_or_create_settings(self, clinic_id: UUID) -> ClinicNotificationSetting:
        stmt = select(ClinicNotificationSetting).where(
            ClinicNotificationSetting.clinic_id == clinic_id,
            ClinicNotificationSetting.deleted_at.is_(None),
        )
        setting = await self.db.scalar(stmt)
        if not setting:
            setting = ClinicNotificationSetting(
                id=uuid4(),
                clinic_id=clinic_id,
                enable_email=True,
                enable_sms=True,
                enable_whatsapp=False,
                reminder_intervals_hours="168,72,24,2",
            )
            self.db.add(setting)
            await self.db.flush()
        return setting

    async def update_settings(
        self, setting: ClinicNotificationSetting | UUID, payload: ClinicNotificationSettingUpdate, actor_id: UUID | None = None
    ) -> ClinicNotificationSetting:
        if isinstance(setting, UUID):
            setting = await self.get_or_create_settings(setting)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(setting, field, value)
        setting.updated_by = actor_id
        await self.db.flush()
        return setting
