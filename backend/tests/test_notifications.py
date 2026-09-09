from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Clinic, Role, User
from app.models.notification import (
    ClinicNotificationSetting,
    DeliveryChannel,
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)
from app.models.patient import Patient
from app.models.treatment import FollowUpStatus, Treatment, TreatmentFollowUp
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    ClinicNotificationSettingUpdate,
    NotificationBulkCreate,
    NotificationCreate,
)
from app.services.notifications.followup_service import FollowUpRecallService
from app.services.notifications.notification_service import NotificationService
from app.services.notifications.reminder_service import AppointmentReminderService
from app.services.notifications.template_engine import NotificationTemplateEngine


class FakeNotifDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        for it in self.added:
            if getattr(it, "id", None) is None:
                it.id = uuid4()
            if getattr(it, "created_at", None) is None:
                it.created_at = datetime.now(UTC)
            if getattr(it, "updated_at", None) is None:
                it.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for it in self.items:
            if isinstance(it, model) and getattr(it, "id", None) == id_:
                return it
        return None

    async def scalar(self, stmt: object) -> object:
        res = await self.execute(stmt)
        if hasattr(res, "scalar_one_or_none"):
            return res.scalar_one_or_none()
        return None

    async def execute(self, stmt: object) -> object:
        text = str(stmt).lower()
        from types import SimpleNamespace

        if "from notifications" in text:
            notifs = [i for i in self.items if isinstance(i, Notification) and i.deleted_at is None]
            if "group_by" in text or "group by" in text:
                return SimpleNamespace(all=list)
            if "count(" in text:
                if "is_read is false" in text or "is_read = false" in text:
                    unread = [n for n in notifs if not n.is_read]
                    return SimpleNamespace(scalar_one_or_none=lambda: len(unread))
                return SimpleNamespace(scalar_one_or_none=lambda: len(notifs))
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: notifs, first=lambda: notifs[0] if notifs else None),
                scalar_one_or_none=lambda: notifs[0] if notifs else None,
                all=list,
            )

        if "from notification_templates" in text:
            tmpls = [i for i in self.items if isinstance(i, NotificationTemplate) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: tmpls, first=lambda: tmpls[0] if tmpls else None),
                scalar_one_or_none=lambda: tmpls[0] if tmpls else None,
                all=list,
            )

        if "from clinic_notification_settings" in text:
            sets = [i for i in self.items if isinstance(i, ClinicNotificationSetting)]
            return SimpleNamespace(scalar_one_or_none=lambda: sets[0] if sets else None)

        if "from appointments" in text:
            appts = [i for i in self.items if isinstance(i, Appointment) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: appts),
                scalar_one_or_none=lambda: appts[0] if appts else None,
            )

        if "from treatment_follow_ups" in text:
            fups = [i for i in self.items if isinstance(i, TreatmentFollowUp) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: fups),
                scalar_one_or_none=lambda: fups[0] if fups else None,
            )

        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic)]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: pats[0] if pats else None,
                scalars=lambda: SimpleNamespace(all=lambda: pats),
            )

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=list),
            scalar_one_or_none=lambda: None,
        )


@pytest.fixture
def base_entities():
    clinic_id = uuid4()
    clinic = Clinic(id=clinic_id, name="Pro Smile Dental", slug="pro-smile", is_active=True)
    staff = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="reception@prosmile.com",
        first_name="Alice",
        last_name="Staff",
        role=Role.RECEPTIONIST,
        is_active=True,
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        first_name="John",
        last_name="Doe",
        patient_number="P-2026-001",
        mobile_number="+919876543210",
        email="john.doe@example.com",
    )
    return clinic, staff, patient


@pytest.mark.asyncio
async def test_template_engine_rendering():
    engine = NotificationTemplateEngine()
    rendered = engine.render_text("Hello {{patient_name}}, your clinic is {{clinic_name}}.", {
        "patient_name": "Sarah Connor",
        "clinic_name": "Cyberdyne Dental",
    })
    assert rendered == "Hello Sarah Connor, your clinic is Cyberdyne Dental."

    # Test missing variable fallback
    rendered_missing = engine.render_text("Hello {{name}}, code is {{code}}", {"name": "Bob"})
    assert rendered_missing == "Hello Bob, code is "


@pytest.mark.asyncio
async def test_notification_service_send_and_read(base_entities):
    clinic, staff, patient = base_entities
    db = FakeNotifDb([clinic, staff, patient])
    service = NotificationService(db)

    payload = NotificationCreate(
        notification_type=NotificationType.APPOINTMENT_REMINDER,
        priority=NotificationPriority.HIGH,
        delivery_channel=DeliveryChannel.IN_APP,
        recipient_user_id=staff.id,
        patient_id=patient.id,
        title="Upcoming Visit Reminder",
        message="Please be present 10 mins before your slot.",
    )

    notif = await service.send_notification(clinic.id, payload, actor=staff)
    assert notif.id is not None
    assert notif.status in (NotificationStatus.SENT, NotificationStatus.DELIVERED)
    assert not notif.is_read

    # Mark as read
    read_notif = await service.mark_notification_as_read(clinic.id, notif.id)
    assert read_notif.is_read
    assert read_notif.read_at is not None


@pytest.mark.asyncio
async def test_notification_bulk_send(base_entities):
    clinic, staff, patient = base_entities
    db = FakeNotifDb([clinic, staff, patient])
    service = NotificationService(db)

    bulk = NotificationBulkCreate(
        notifications=[
            NotificationCreate(
                notification_type=NotificationType.SYSTEM_ALERT,
                priority=NotificationPriority.NORMAL,
                delivery_channel=DeliveryChannel.IN_APP,
                recipient_user_id=staff.id,
                title="Alert 1",
                message="Maintenance Notice 1",
            ),
            NotificationCreate(
                notification_type=NotificationType.SYSTEM_ALERT,
                priority=NotificationPriority.NORMAL,
                delivery_channel=DeliveryChannel.EMAIL,
                recipient_user_id=staff.id,
                title="Alert 2",
                message="Maintenance Notice 2",
            ),
        ]
    )

    created = await service.send_bulk_notifications(clinic.id, bulk)
    assert len(created) == 2
    assert created[0].delivery_channel == DeliveryChannel.IN_APP
    assert created[1].delivery_channel == DeliveryChannel.EMAIL


@pytest.mark.asyncio
async def test_appointment_reminder_service(base_entities):
    clinic, staff, patient = base_entities
    target_dt = datetime.now(UTC) + timedelta(hours=24)
    appt = Appointment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=staff.id,
        chair_id=uuid4(),
        appointment_number="APT-001",
        date=target_dt.date(),
        start_time=target_dt.time().replace(microsecond=0),
        end_time=(target_dt + timedelta(minutes=30)).time().replace(microsecond=0),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        visit_type=VisitType.CONSULTATION,
    )
    appt.patient = patient
    appt.dentist = staff

    db = FakeNotifDb([clinic, staff, patient, appt])
    reminder_svc = AppointmentReminderService(db)
    result = await reminder_svc.scan_and_send_reminders(clinic.id)

    assert result.scanned_appointments >= 1
    assert result.reminders_created >= 1


@pytest.mark.asyncio
async def test_followup_recall_service(base_entities):
    clinic, staff, patient = base_entities
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        appointment_id=uuid4(),
        dentist_id=staff.id,
        treatment_number="TRT-001",
        diagnosis="Pulpitis",
        treatment_plan="Root Canal Therapy #19",
    )
    due_date = datetime.now(UTC).date() + timedelta(days=3)
    followup = TreatmentFollowUp(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        follow_up_date=due_date,
        reason="Check tooth sensitivity and healing",
        status=FollowUpStatus.SCHEDULED,
    )
    followup.patient = patient
    followup.treatment = treatment

    db = FakeNotifDb([clinic, staff, patient, treatment, followup])
    followup_svc = FollowUpRecallService(db)
    result = await followup_svc.scan_and_send_followups(clinic.id)

    assert result.scanned_followups >= 1
    assert result.reminders_created >= 1


@pytest.mark.asyncio
async def test_notification_repository_stats_and_settings(base_entities):
    clinic, staff, patient = base_entities
    db = FakeNotifDb([clinic, staff, patient])
    repo = NotificationRepository(db)

    settings = await repo.get_or_create_settings(clinic.id)
    assert settings.enable_email
    assert settings.reminder_intervals_hours == "168,72,24,2"

    updated_settings = await repo.update_settings(
        clinic.id,
        ClinicNotificationSettingUpdate(
            enable_sms=True,
            enable_whatsapp=True,
            reminder_intervals_hours="48,24,2",
        ),
    )
    assert updated_settings.enable_sms
    assert updated_settings.enable_whatsapp
    assert updated_settings.reminder_intervals_hours == "48,24,2"

    stats = await repo.get_notification_stats(clinic.id)
    assert "total_count" in stats
    assert "unread_count" in stats
