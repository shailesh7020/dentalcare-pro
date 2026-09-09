from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import Clinic, User
from app.models.notification import (
    DeliveryChannel,
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.models.treatment import FollowUpStatus, Treatment, TreatmentFollowUp
from app.schemas.notification import FollowUpProcessResult, NotificationCreate
from app.services.notifications.notification_service import NotificationService

PROCEDURE_RECALL_DAYS: dict[str, int] = {
    "root canal": 7,
    "extraction": 7,
    "surgical": 7,
    "scaling": 180,  # 6 months
    "polishing": 180,
    "implant": 90,   # 3 months
    "crown": 365,    # 1 year
    "bridge": 365,
    "orthodontic": 30, # 1 month
}


class FollowUpService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notif_service = NotificationService(db)

    async def generate_followups_for_treatment(
        self, clinic_id: UUID, treatment_id: UUID, dentist: User
    ) -> list[TreatmentFollowUp]:
        """Automatically generates follow-up schedule records based on completed treatment procedures."""
        stmt = (
            select(Treatment)
            .options(
                selectinload(Treatment.procedures),
                selectinload(Treatment.patient),
            )
            .where(
                Treatment.id == treatment_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
        )
        treatment = await self.db.scalar(stmt)
        if not treatment:
            return []

        created_followups: list[TreatmentFollowUp] = []
        today = datetime.now(UTC).date()

        for proc in treatment.procedures:
            p_name = proc.procedure_name.lower()
            days = 14  # default 2 weeks

            for key, val in PROCEDURE_RECALL_DAYS.items():
                if key in p_name:
                    days = val
                    break

            f_date = today + timedelta(days=days)
            follow_up = TreatmentFollowUp(
                id=uuid4(),
                treatment_id=treatment.id,
                clinic_id=clinic_id,
                patient_id=treatment.patient_id,
                follow_up_date=f_date,
                reason=f"Clinical review for {proc.procedure_name}",
                instructions=f"Post-op review scheduled {days} days following treatment.",
                status=FollowUpStatus.SCHEDULED,
            )
            self.db.add(follow_up)
            created_followups.append(follow_up)

        await self.db.commit()
        return created_followups

    async def process_due_followups(self, clinic_id: UUID) -> FollowUpProcessResult:
        """
        Scans upcoming treatment follow-up records due within the next 7 days
        and dispatches FOLLOW_UP_REMINDER notifications to patients.
        """
        today = datetime.now(UTC).date()
        target_date = today + timedelta(days=7)

        stmt = (
            select(TreatmentFollowUp)
            .options(
                selectinload(TreatmentFollowUp.patient),
                selectinload(TreatmentFollowUp.treatment),
            )
            .where(
                TreatmentFollowUp.clinic_id == clinic_id,
                TreatmentFollowUp.status == FollowUpStatus.SCHEDULED,
                TreatmentFollowUp.follow_up_date <= target_date,
                TreatmentFollowUp.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        followups = list(res.scalars().all())

        clinic = await self.db.get(Clinic, clinic_id)
        clinic_name = clinic.name if clinic else "DentalCare Pro"
        clinic_phone = clinic.phone if clinic else "+91 99000 11223"

        scanned = len(followups)
        created = 0

        for f in followups:
            if not f.patient:
                continue

            tag = f"followup_{f.id}"
            # Check duplicate
            dup_check = select(Notification.id).where(
                Notification.clinic_id == clinic_id,
                Notification.patient_id == f.patient_id,
                Notification.notification_type == NotificationType.FOLLOW_UP_REMINDER,
                Notification.data_json.like(f"%{tag}%"),
            ).limit(1)
            if await self.db.scalar(dup_check):
                continue

            ctx = {
                "patient_name": f"{f.patient.first_name} {f.patient.last_name}",
                "procedure_name": f.reason,
                "follow_up_date": f.follow_up_date.strftime("%d %b %Y"),
                "clinic_name": clinic_name,
                "clinic_phone": clinic_phone,
            }

            payload = NotificationCreate(
                notification_type=NotificationType.FOLLOW_UP_REMINDER,
                priority=NotificationPriority.NORMAL,
                delivery_channel=DeliveryChannel.IN_APP,
                patient_id=f.patient_id,
                title=f"Clinical Follow-Up Due: {clinic_name}",
                message=f"Dear {ctx['patient_name']}, your clinical check for {f.reason} is due on {ctx['follow_up_date']}.",
                data_json=json.dumps({"follow_up_id": str(f.id), "tag": tag}),
            )
            await self.notif_service.send_notification(clinic_id, payload, context=ctx)
            created += 1

        return FollowUpProcessResult(scanned_followups=scanned, reminders_created=created)

    async def scan_and_send_followups(self, clinic_id: UUID) -> FollowUpProcessResult:
        return await self.process_due_followups(clinic_id)


FollowUpRecallService = FollowUpService


