from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user, require_roles
from app.models.identity import Role, User
from app.models.notification import (
    DeliveryChannel,
    NotificationPriority,
    NotificationType,
)
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    ClinicNotificationSettingRead,
    ClinicNotificationSettingUpdate,
    FollowUpProcessResult,
    NotificationBulkCreate,
    NotificationCreate,
    NotificationRead,
    NotificationStatsRead,
    NotificationTemplateCreate,
    NotificationTemplateRead,
    NotificationTemplateUpdate,
    ReminderProcessResult,
)
from app.services.notifications.followup_service import FollowUpRecallService
from app.services.notifications.notification_service import NotificationService
from app.services.notifications.reminder_service import AppointmentReminderService

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])

STAFF_ROLES = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
]

ADMIN_ROLES = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN]


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = Query(default=False),
    channel: DeliveryChannel | None = Query(default=None),
    notification_type: NotificationType | None = Query(default=None),
    priority: NotificationPriority | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    
    repo = NotificationRepository(db)
    user_id = actor.id if actor.role == Role.PATIENT else None
    patient_id = actor.patient_id if actor.role == Role.PATIENT else None

    notifications = await repo.list_notifications(
        clinic_id=actor.clinic_id,
        user_id=user_id,
        patient_id=patient_id,
        unread_only=unread_only,
        channel=channel,
        notification_type=notification_type,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    if not actor.clinic_id:
        return {"unread_count": 0}
    repo = NotificationRepository(db)
    user_id = actor.id if actor.role == Role.PATIENT else None
    patient_id = actor.patient_id if actor.role == Role.PATIENT else None
    count = await repo.get_unread_count(actor.clinic_id, user_id=user_id, patient_id=patient_id)
    return {"unread_count": count}


@router.get("/stats", response_model=NotificationStatsRead)
async def get_notification_stats(
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> NotificationStatsRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    stats = await repo.get_notification_stats(actor.clinic_id)
    return NotificationStatsRead(**stats)


@router.get("/templates", response_model=list[NotificationTemplateRead])
async def list_templates(
    channel: DeliveryChannel | None = Query(default=None),
    notification_type: NotificationType | None = Query(default=None),
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationTemplateRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    templates = await repo.list_templates(actor.clinic_id, channel=channel, notification_type=notification_type)
    return [NotificationTemplateRead.model_validate(t) for t in templates]


@router.post("/templates", response_model=NotificationTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: NotificationTemplateCreate,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> NotificationTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    tmpl = await repo.create_template(actor.clinic_id, payload)
    await db.commit()
    return NotificationTemplateRead.model_validate(tmpl)


@router.get("/templates/{template_id}", response_model=NotificationTemplateRead)
async def get_template(
    template_id: UUID,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> NotificationTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    tmpl = await repo.get_template(actor.clinic_id, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Notification template not found.")
    return NotificationTemplateRead.model_validate(tmpl)


@router.put("/templates/{template_id}", response_model=NotificationTemplateRead)
async def update_template(
    template_id: UUID,
    payload: NotificationTemplateUpdate,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> NotificationTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    tmpl = await repo.update_template(actor.clinic_id, template_id, payload)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Notification template not found.")
    await db.commit()
    return NotificationTemplateRead.model_validate(tmpl)


@router.get("/settings", response_model=ClinicNotificationSettingRead)
async def get_settings(
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ClinicNotificationSettingRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    settings = await repo.get_or_create_settings(actor.clinic_id)
    return ClinicNotificationSettingRead.model_validate(settings)


@router.put("/settings", response_model=ClinicNotificationSettingRead)
async def update_settings(
    payload: ClinicNotificationSettingUpdate,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ClinicNotificationSettingRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    repo = NotificationRepository(db)
    settings = await repo.update_settings(actor.clinic_id, payload)
    await db.commit()
    return ClinicNotificationSettingRead.model_validate(settings)


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationCreate,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = NotificationService(db)
    notif = await service.send_notification(actor.clinic_id, payload)
    return NotificationRead.model_validate(notif)


@router.post("/bulk", response_model=list[NotificationRead], status_code=status.HTTP_201_CREATED)
async def send_bulk_notifications(
    payload: NotificationBulkCreate,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = NotificationService(db)
    results = await service.send_bulk_notifications(actor.clinic_id, payload)
    return [NotificationRead.model_validate(n) for n in results]


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_as_read(
    notification_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = NotificationService(db)
    notif = await service.mark_notification_as_read(actor.clinic_id, notification_id)
    return NotificationRead.model_validate(notif)


@router.post("/mark-all-read")
async def mark_all_as_read(
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    if not actor.clinic_id:
        return {"updated": 0}
    repo = NotificationRepository(db)
    user_id = actor.id if actor.role == Role.PATIENT else None
    patient_id = actor.patient_id if actor.role == Role.PATIENT else None
    count = await repo.mark_all_as_read(actor.clinic_id, user_id=user_id, patient_id=patient_id)
    await db.commit()
    return {"updated": count}


@router.post("/run-reminders", response_model=ReminderProcessResult)
async def trigger_appointment_reminders(
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ReminderProcessResult:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    reminder_svc = AppointmentReminderService(db)
    return await reminder_svc.scan_and_send_reminders(actor.clinic_id)


@router.post("/run-followups", response_model=FollowUpProcessResult)
async def trigger_followup_recalls(
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> FollowUpProcessResult:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    followup_svc = FollowUpRecallService(db)
    return await followup_svc.scan_and_send_followups(actor.clinic_id)
