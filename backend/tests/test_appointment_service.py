from datetime import date, time
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    Chair,
    ChairStatus,
    VisitType,
)
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient, PatientTimelineEvent
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentUpdate,
    ChairCreate,
    ChairUpdate,
)
from app.services.appointment_service import AppointmentService
from app.services.chair_service import ChairService


class FakeDb:
    def __init__(self, items=None):
        self.items = items or []
        self.added = []
        self.commits = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        pass

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        pass

    async def get(self, model, id_):
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def scalar(self, query):
        text_query = str(query).lower()
        if "count(" in text_query:
            return 1
        for item in self.items:
            if "chairs" in text_query and isinstance(item, Chair):
                return item
            if "users" in text_query and isinstance(item, User):
                return item
            if "patients" in text_query and isinstance(item, Patient):
                return item
            if "appointments" in text_query and isinstance(item, Appointment):
                return item
        return None

    async def scalars(self, query):
        class Rows:
            def __init__(self, val):
                self.val = val

            def all(self):
                return self.val

        text_query = str(query).lower()
        if "chairs" in text_query:
            return Rows([i for i in self.items if isinstance(i, Chair)])
        if "users" in text_query:
            return Rows([i for i in self.items if isinstance(i, User)])
        if "appointments" in text_query:
            return Rows([i for i in self.items if isinstance(i, Appointment)])
        return Rows(self.items)

    async def execute(self, query):
        class Rows:
            def all(self):
                return [(AppointmentStatus.COMPLETED, 1)]

        return Rows()


def setup_test_entities(clinic_id):
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-001",
        first_name="Pooja",
        last_name="Hegde",
        gender="FEMALE",
        date_of_birth=date(1995, 3, 12),
        mobile_number="9876543210",
        email="pooja@example.com",
    )
    patient.medical_history = MedicalHistory(patient_id=patient.id, cardiac_disease=True)

    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.dentist@example.com",
        password_hash="hash",
        first_name="Vikram",
        last_name="Malhotra",
        role=Role.DENTIST,
        is_active=True,
    )

    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@example.com",
        password_hash="hash",
        first_name="Admin",
        last_name="User",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )

    chair = Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Chair 1",
        room_number="Suite 101",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )

    return patient, dentist, admin, chair


@pytest.mark.asyncio
async def test_create_appointment_success():
    clinic_id = uuid4()
    patient, dentist, admin, chair = setup_test_entities(clinic_id)
    db = FakeDb([patient, dentist, admin, chair])
    service = AppointmentService(db)

    async def no_conflicts(**kwargs):
        return {
            "dentist_conflict": None,
            "chair_conflict": None,
            "patient_conflict": None,
            "blocked_conflict": None,
        }
    service.repo.check_conflicts = no_conflicts

    payload = AppointmentCreate(
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        date=date(2026, 9, 10),
        start_time=time(10, 0),
        duration=30,
        visit_type=VisitType.CONSULTATION,
        chief_complaint="Checkup",
    )

    res = await service.create(clinic_id, payload, admin)
    assert res.appointment_number.startswith("APT-20260910-")
    assert any(isinstance(x, PatientTimelineEvent) for x in db.added)


@pytest.mark.asyncio
async def test_create_appointment_availability_conflict_and_admin_override():
    clinic_id = uuid4()
    patient, dentist, admin, chair = setup_test_entities(clinic_id)
    conflicting_apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-EXISTING-01",
        date=date(2026, 9, 10),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        visit_type=VisitType.CONSULTATION,
        patient=patient,
        dentist=dentist,
        chair=chair,
        timeline_events=[],
    )

    db = FakeDb([patient, dentist, admin, chair, conflicting_apt])
    service = AppointmentService(db)

    # Return dentist conflict
    async def dentist_conflict(**kwargs):
        return {
            "dentist_conflict": conflicting_apt,
            "chair_conflict": None,
            "patient_conflict": None,
            "blocked_conflict": None,
        }
    service.repo.check_conflicts = dentist_conflict

    payload = AppointmentCreate(
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        date=date(2026, 9, 10),
        start_time=time(10, 0),
        duration=30,
        visit_type=VisitType.EMERGENCY,
        is_emergency_override=False,
    )

    # Non-override fails with 409
    with pytest.raises(HTTPException) as exc_info:
        await service.create(clinic_id, payload, admin)
    assert exc_info.value.status_code == 409
    assert "Dentist conflict" in exc_info.value.detail

    # Emergency override by non-admin still fails with 409
    payload.is_emergency_override = True
    with pytest.raises(HTTPException) as exc_info:
        await service.create(clinic_id, payload, dentist)
    assert exc_info.value.status_code == 409

    # Emergency override by CLINIC_ADMIN succeeds!
    res = await service.create(clinic_id, payload, admin)
    assert res is not None


@pytest.mark.asyncio
async def test_completed_appointment_immutability():
    clinic_id = uuid4()
    patient, dentist, admin, chair = setup_test_entities(clinic_id)
    apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration=30,
        status=AppointmentStatus.COMPLETED,
        patient=patient,
        dentist=dentist,
        chair=chair,
        timeline_events=[],
    )

    db = FakeDb([patient, dentist, admin, chair, apt])
    service = AppointmentService(db)

    # 1. Update completed appointment fails
    with pytest.raises(HTTPException) as exc_info:
        await service.update(
            clinic_id, apt.id, AppointmentUpdate(notes="Trying to edit after complete"), admin
        )
    assert exc_info.value.status_code == 400
    assert "Completed appointments cannot be modified" in exc_info.value.detail

    # 2. Cancel completed appointment fails
    with pytest.raises(HTTPException) as exc_info:
        await service.cancel(clinic_id, apt.id, AppointmentCancel(reason="Cancel completed"), admin)
    assert exc_info.value.status_code == 400

    # 3. Reschedule completed appointment fails
    with pytest.raises(HTTPException) as exc_info:
        await service.reschedule(
            clinic_id,
            apt.id,
            AppointmentReschedule(
                new_date=date(2026, 9, 9), new_start_time=time(10, 0), reason="Reschedule"
            ),
            admin,
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_appointment_state_transitions():
    clinic_id = uuid4()
    patient, dentist, admin, chair = setup_test_entities(clinic_id)
    apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260908-0002",
        date=date(2026, 9, 8),
        start_time=time(11, 0),
        end_time=time(11, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        patient=patient,
        dentist=dentist,
        chair=chair,
        timeline_events=[],
    )

    db = FakeDb([patient, dentist, admin, chair, apt])
    service = AppointmentService(db)

    # 1. Confirm
    confirmed = await service.confirm(clinic_id, apt.id, admin)
    assert confirmed.status == AppointmentStatus.CONFIRMED

    # 2. Check in
    checked_in = await service.checkin(clinic_id, apt.id, admin)
    assert checked_in.status == AppointmentStatus.CHECKED_IN

    # 3. Start treatment
    in_treatment = await service.start_treatment(clinic_id, apt.id, admin)
    assert in_treatment.status == AppointmentStatus.IN_TREATMENT

    # 4. Complete
    completed = await service.complete(clinic_id, apt.id, admin)
    assert completed.status == AppointmentStatus.COMPLETED

    # Verify PatientTimelineEvent was emitted on completion
    assert any(
        isinstance(x, PatientTimelineEvent) and x.event_type == "APPOINTMENT_COMPLETED"
        for x in db.added
    )


@pytest.mark.asyncio
async def test_appointment_cancellation_and_reschedule():
    clinic_id = uuid4()
    patient, dentist, admin, chair = setup_test_entities(clinic_id)
    apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260908-0003",
        date=date(2026, 9, 8),
        start_time=time(14, 0),
        end_time=time(14, 30),
        duration=30,
        status=AppointmentStatus.CONFIRMED,
        patient=patient,
        dentist=dentist,
        chair=chair,
        timeline_events=[],
    )

    db = FakeDb([patient, dentist, admin, chair, apt])
    service = AppointmentService(db)
    async def no_conflicts_reschedule(**kwargs):
        return {
            "dentist_conflict": None,
            "chair_conflict": None,
            "patient_conflict": None,
            "blocked_conflict": None,
        }
    service.repo.check_conflicts = no_conflicts_reschedule

    # Reschedule
    rescheduled = await service.reschedule(
        clinic_id=clinic_id,
        appointment_id=apt.id,
        payload=AppointmentReschedule(
            new_date=date(2026, 9, 9),
            new_start_time=time(15, 0),
            reason="Patient requested afternoon slot",
        ),
        actor=admin,
    )
    assert rescheduled.status == AppointmentStatus.RESCHEDULED

    # Cancel
    cancelled = await service.cancel(
        clinic_id=clinic_id,
        appointment_id=apt.id,
        payload=AppointmentCancel(reason="Illness"),
        actor=admin,
    )
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert any(
        isinstance(x, PatientTimelineEvent) and x.event_type == "APPOINTMENT_CANCELLED"
        for x in db.added
    )


@pytest.mark.asyncio
async def test_chair_service_crud_and_conflict():
    clinic_id = uuid4()
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@example.com",
        password_hash="hash",
        first_name="Admin",
        last_name="User",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )
    existing_chair = Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Chair 1",
        room_number="101",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )

    db = FakeDb([admin, existing_chair])
    service = ChairService(db)

    # 1. Duplicate name fails with 409
    with pytest.raises(HTTPException) as exc_info:
        await service.create(
            clinic_id, ChairCreate(name="Chair 1", room_number="102"), admin
        )
    assert exc_info.value.status_code == 409

    # 2. Get chair
    chair = await service.get(clinic_id, existing_chair.id)
    assert chair.name == "Chair 1"

    # 3. Update chair
    updated = await service.update(
        clinic_id, existing_chair.id, ChairUpdate(name="Operatory 1"), admin
    )
    assert updated.name == "Operatory 1"
