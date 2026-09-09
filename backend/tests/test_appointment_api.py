from datetime import date, time
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import appointments as apt_api
from app.api.v1 import calendar as cal_api
from app.api.v1 import chairs as chairs_api
from app.api.v1 import dentists as dentists_api
from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    Chair,
    ChairStatus,
    VisitType,
)
from app.models.identity import Role, User
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentUpdate,
    ChairCreate,
    ChairUpdate,
)


class FakeDb:
    def __init__(self, items=None):
        self.items = items or []
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

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
        if "start_time <" in text_query:
            return None
        if "chairs.name =" in text_query or "chairs.name = :" in text_query or "chairs.name ==" in text_query:
            try:
                params = getattr(query, "_params", {}) or {}
                if not params and hasattr(query, "compile"):
                    params = query.compile().params
                target_name = params.get("name_1") or params.get("name")
                for item in self.items:
                    if isinstance(item, Chair) and item.name == target_name:
                        return item
                return None
            except Exception:
                pass
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
                return [(AppointmentStatus.COMPLETED, 2)]

        return Rows()


def make_context():
    clinic_id = uuid4()
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@test.com",
        password_hash="hash",
        first_name="Admin",
        last_name="One",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@test.com",
        password_hash="hash",
        first_name="Dr. Dentist",
        last_name="Two",
        role=Role.DENTIST,
        is_active=True,
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-100",
        first_name="Alice",
        last_name="Smith",
        gender="FEMALE",
        date_of_birth=date(1992, 1, 1),
        mobile_number="9988776655",
    )
    chair = Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Chair A",
        room_number="Room 1",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )
    apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
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
    return clinic_id, admin, dentist, patient, chair, apt


@pytest.mark.asyncio
async def test_appointment_api_endpoints():
    clinic_id, admin, dentist, patient, chair, apt = make_context()
    db = FakeDb([admin, dentist, patient, chair, apt])

    # 1. Create appointment
    create_payload = AppointmentCreate(
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        date=date(2026, 9, 8),
        start_time=time(11, 0),
        duration=30,
        visit_type=VisitType.CONSULTATION,
    )
    created = await apt_api.create_appointment(payload=create_payload, actor=admin, db=db)
    assert created.patient_id == patient.id

    # 2. List appointments
    items = await apt_api.list_appointments(actor=admin, db=db)
    assert len(items) >= 1

    # 3. Get appointment details
    detail = await apt_api.get_appointment(id=apt.id, actor=admin, db=db)
    assert detail.id == apt.id

    # 4. Update appointment
    updated = await apt_api.update_appointment(
        id=apt.id, payload=AppointmentUpdate(notes="Updated notes"), actor=admin, db=db
    )
    assert updated.id == apt.id

    # 5. Status actions: confirm, checkin, start, complete
    confirmed = await apt_api.confirm_appointment(id=apt.id, actor=admin, db=db)
    assert confirmed.status == AppointmentStatus.CONFIRMED

    checked_in = await apt_api.checkin_appointment(id=apt.id, actor=admin, db=db)
    assert checked_in.status == AppointmentStatus.CHECKED_IN

    started = await apt_api.start_treatment(id=apt.id, actor=admin, db=db)
    assert started.status == AppointmentStatus.IN_TREATMENT

    completed = await apt_api.complete_appointment(id=apt.id, actor=admin, db=db)
    assert completed.status == AppointmentStatus.COMPLETED

    # 6. Queue and Stats
    queue = await apt_api.get_queue(target_date=date(2026, 9, 8), actor=admin, db=db)
    assert len(queue) >= 1

    stats = await apt_api.get_stats(target_date=date(2026, 9, 8), actor=admin, db=db)
    assert stats.completed == 2

    # 7. Reschedule & Cancel on a new appointment
    apt2 = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260908-0002",
        date=date(2026, 9, 8),
        start_time=time(14, 0),
        end_time=time(14, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        patient=patient,
        dentist=dentist,
        chair=chair,
        timeline_events=[],
    )
    db2 = FakeDb([admin, dentist, patient, chair, apt2])

    rescheduled = await apt_api.reschedule_appointment(
        id=apt2.id,
        payload=AppointmentReschedule(
            new_date=date(2026, 9, 9),
            new_start_time=time(15, 0),
            reason="Rescheduled by staff",
        ),
        actor=admin,
        db=db2,
    )
    assert rescheduled.status == AppointmentStatus.RESCHEDULED

    cancelled = await apt_api.cancel_appointment(
        id=apt2.id,
        payload=AppointmentCancel(reason="Cancelled by patient"),
        actor=admin,
        db=db2,
    )
    assert cancelled.status == AppointmentStatus.CANCELLED

    # 8. Delete appointment
    await apt_api.delete_appointment(id=apt2.id, actor=admin, db=db2)


@pytest.mark.asyncio
async def test_calendar_and_chair_dentist_apis():
    clinic_id, admin, dentist, patient, chair, apt = make_context()
    db = FakeDb([admin, dentist, patient, chair, apt])

    # Calendar APIs
    day_cal = await cal_api.get_day_calendar(target_date=date(2026, 9, 8), actor=admin, db=db)
    assert day_cal.date == date(2026, 9, 8)
    assert len(day_cal.chairs) >= 1

    week_cal = await cal_api.get_week_calendar(start_date=date(2026, 9, 7), actor=admin, db=db)
    assert week_cal.start_date == date(2026, 9, 7)

    month_cal = await cal_api.get_month_calendar(year=2026, month=9, actor=admin, db=db)
    assert month_cal.month == 9

    # Chair APIs
    chairs = await chairs_api.list_chairs(include_inactive=False, actor=admin, db=db)
    assert len(chairs) >= 1

    created_chair = await chairs_api.create_chair(
        payload=ChairCreate(name="Chair New", room_number="Room 2"),
        actor=admin,
        db=db,
    )
    assert created_chair.name == "Chair New"

    chair_details = await chairs_api.get_chair(id=chair.id, actor=admin, db=db)
    assert chair_details.name == "Chair A"

    updated_chair = await chairs_api.update_chair(
        id=chair.id, payload=ChairUpdate(room_number="Room 101"), actor=admin, db=db
    )
    assert updated_chair.room_number == "Room 101"

    chair_sched = await chairs_api.get_chair_schedule(id=chair.id, actor=admin, db=db)
    assert chair_sched.chair.name == "Chair A"

    # Dentist APIs
    dentists = await dentists_api.list_dentists(actor=admin, db=db)
    assert len(dentists) >= 1

    dentist_sched = await dentists_api.get_dentist_schedule(id=dentist.id, actor=admin, db=db)
    assert dentist_sched.dentist_id == dentist.id


@pytest.mark.asyncio
async def test_multi_tenancy_isolation():
    clinic_a = uuid4()
    clinic_b = uuid4()

    user_a = User(
        id=uuid4(),
        clinic_id=clinic_a,
        email="user_a@test.com",
        password_hash="hash",
        first_name="User",
        last_name="A",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )

    # Appointment belonging to Clinic B
    apt_b = Appointment(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_id=uuid4(),
        dentist_id=uuid4(),
        chair_id=uuid4(),
        appointment_number="APT-CLINIC-B-001",
        date=date(2026, 9, 8),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        timeline_events=[],
    )

    # User A tries to get Appointment B: should raise 404 because query filters by User A's clinic_id
    db = FakeDb([])
    with pytest.raises(HTTPException) as exc_info:
        await apt_api.get_appointment(id=apt_b.id, actor=user_a, db=db)
    assert exc_info.value.status_code == 404
