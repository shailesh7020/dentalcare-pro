from datetime import date, datetime, time
from uuid import uuid4

import pytest

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentTimelineEvent,
    Chair,
    ChairStatus,
    VisitType,
)
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.chair_repository import ChairRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    ChairCreate,
    ChairUpdate,
)


class ScalarRows:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class FakeDb:
    def __init__(self, items=None, scalar_return=None):
        self.items = items or []
        self.scalar_return = scalar_return
        self.added = []
        self.flushes = 0
        self.commits = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushes += 1

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        pass

    async def scalar(self, query):
        if self.scalar_return is not None:
            return self.scalar_return
        return self.items[0] if self.items else None

    async def scalars(self, query):
        return ScalarRows(self.items)

    async def get(self, model, id_):
        for item in self.items:
            if getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, query):
        # Used for group_by status in get_dashboard_stats
        return ScalarRows([(AppointmentStatus.COMPLETED, 3), (AppointmentStatus.CHECKED_IN, 2)])


def sample_patient(clinic_id):
    p = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-001",
        first_name="Rohan",
        last_name="Verma",
        gender="MALE",
        date_of_birth=date(1990, 5, 20),
        mobile_number="9876543210",
    )
    p.medical_history = MedicalHistory(
        patient_id=p.id,
        cardiac_disease=True,
        hypertension=True,
        diabetes=False,
        asthma=True,
        epilepsy=False,
        pregnancy=False,
        allergies="Penicillin, Latex",
    )
    return p


def sample_dentist(clinic_id):
    return User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@example.com",
        password_hash="hash",
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
        is_active=True,
    )


def sample_chair(clinic_id):
    return Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Chair 1",
        room_number="101",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )


def sample_appointment(clinic_id, patient, dentist, chair):
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
        priority="NORMAL",
        chief_complaint="Toothache",
        is_emergency_override=False,
    )
    apt.patient = patient
    apt.dentist = dentist
    apt.chair = chair
    apt.timeline_events = [
        AppointmentTimelineEvent(
            id=uuid4(),
            appointment_id=apt.id,
            clinic_id=clinic_id,
            from_status=None,
            to_status="SCHEDULED",
            event_type="CREATED",
            title="Appointment Created",
            created_at=datetime.now(),
        )
    ]
    return apt


@pytest.mark.asyncio
async def test_appointment_read_and_detail_models():
    clinic_id = uuid4()
    p = sample_patient(clinic_id)
    d = sample_dentist(clinic_id)
    c = sample_chair(clinic_id)
    apt = sample_appointment(clinic_id, p, d, c)

    repo = AppointmentRepository(FakeDb([apt]))
    read_model = repo.to_read_model(apt)
    assert read_model.appointment_number == "APT-20260908-0001"
    assert read_model.patient_name == "Rohan Verma"
    assert read_model.dentist_name == "Dr. Ananya Shah"
    assert read_model.chair_name == "Chair 1"

    detail_model = repo.to_detail_model(apt)
    assert "Cardiac Disease" in detail_model.patient_medical_alerts
    assert "Hypertension" in detail_model.patient_medical_alerts
    assert "Asthma" in detail_model.patient_medical_alerts
    assert "Allergy: Penicillin, Latex" in detail_model.patient_medical_alerts
    assert len(detail_model.timeline_events) == 1


@pytest.mark.asyncio
async def test_appointment_conflict_checks():
    clinic_id = uuid4()
    p = sample_patient(clinic_id)
    d = sample_dentist(clinic_id)
    c = sample_chair(clinic_id)
    apt = sample_appointment(clinic_id, p, d, c)

    db = FakeDb([apt])
    repo = AppointmentRepository(db)

    # When db.scalar returns apt, all queries encounter a conflict
    conflicts = await repo.check_conflicts(
        clinic_id=clinic_id,
        dentist_id=d.id,
        chair_id=c.id,
        patient_id=p.id,
        target_date=date(2026, 9, 8),
        start_time=time(10, 15),
        end_time=time(10, 45),
        exclude_id=uuid4(),
    )
    assert conflicts["dentist_conflict"] == apt
    assert conflicts["chair_conflict"] == apt
    assert conflicts["patient_conflict"] == apt

    # When db.scalar returns None, no conflicts
    empty_repo = AppointmentRepository(FakeDb([], scalar_return=None))
    no_conflicts = await empty_repo.check_conflicts(
        clinic_id=clinic_id,
        dentist_id=d.id,
        chair_id=c.id,
        patient_id=p.id,
        target_date=date(2026, 9, 8),
        start_time=time(14, 0),
        end_time=time(14, 30),
    )
    assert no_conflicts["dentist_conflict"] is None
    assert no_conflicts["chair_conflict"] is None
    assert no_conflicts["patient_conflict"] is None


@pytest.mark.asyncio
async def test_appointment_repo_mutations_and_queries():
    clinic_id = uuid4()
    p = sample_patient(clinic_id)
    d = sample_dentist(clinic_id)
    c = sample_chair(clinic_id)
    apt = sample_appointment(clinic_id, p, d, c)

    db = FakeDb([apt])
    repo = AppointmentRepository(db)

    # Count
    db.scalar_return = 5
    count = await repo.count_today_appointments(clinic_id, date(2026, 9, 8))
    assert count == 5
    db.scalar_return = None

    # Create
    created = await repo.create(
        clinic_id=clinic_id,
        appointment_number="APT-20260908-0002",
        payload=AppointmentCreate(
            patient_id=p.id,
            dentist_id=d.id,
            chair_id=c.id,
            date=date(2026, 9, 8),
            start_time=time(11, 0),
            duration=45,
            visit_type=VisitType.ROOT_CANAL,
            chief_complaint="Severe pain",
        ),
        end_time=time(11, 45),
        actor_id=d.id,
    )
    assert created == apt

    # Update
    updated = await repo.update(
        appointment=apt,
        payload=AppointmentUpdate(notes="Updated clinical notes"),
        end_time=time(10, 30),
        actor_id=d.id,
    )
    assert updated == apt

    # Change status
    status_changed = await repo.change_status(
        appointment=apt,
        new_status=AppointmentStatus.CHECKED_IN,
        event_type="CHECKED_IN",
        title="Patient Checked In",
        actor_id=d.id,
    )
    assert status_changed == apt
    assert apt.status == AppointmentStatus.CHECKED_IN

    # Reschedule
    rescheduled = await repo.reschedule(
        appointment=apt,
        new_date=date(2026, 9, 9),
        new_start_time=time(14, 0),
        new_end_time=time(14, 30),
        duration=30,
        new_chair_id=c.id,
        new_dentist_id=d.id,
        reason="Patient request",
        is_emergency_override=False,
        actor_id=d.id,
    )
    assert rescheduled == apt
    assert apt.status == AppointmentStatus.RESCHEDULED

    # Calendars & Queue
    day_cal = await repo.get_day_calendar(clinic_id, date(2026, 9, 8))
    assert len(day_cal) == 1

    week_cal = await repo.get_week_calendar(clinic_id, date(2026, 9, 8), date(2026, 9, 14))
    assert len(week_cal) == 1

    month_cal = await repo.get_month_calendar(clinic_id, 2026, 9)
    assert len(month_cal) == 1

    month_cal_dec = await repo.get_month_calendar(clinic_id, 2026, 12)
    assert len(month_cal_dec) == 1

    queue = await repo.get_reception_queue(clinic_id, date(2026, 9, 8))
    assert len(queue) == 1
    assert queue[0].patient_name == "Rohan Verma"

    # Search & filters
    filtered_list = await repo.list(
        clinic_id=clinic_id,
        patient_id=p.id,
        dentist_id=d.id,
        chair_id=c.id,
        target_date=date(2026, 9, 8),
        search="Rohan",
        sort_asc=False,
    )
    assert len(filtered_list) == 1

    # Dashboard stats
    stats = await repo.get_dashboard_stats(clinic_id, date(2026, 9, 8))
    assert stats.completed == 3
    assert stats.waiting == 2

    # Dentist schedule
    schedule = await repo.get_dentist_schedule(
        clinic_id, d.id, date(2026, 9, 8), date(2026, 9, 14)
    )
    assert schedule.dentist_id == d.id


@pytest.mark.asyncio
async def test_chair_repository():
    clinic_id = uuid4()
    c = sample_chair(clinic_id)
    db = FakeDb([c])
    repo = ChairRepository(db)

    created = await repo.create(
        clinic_id=clinic_id,
        payload=ChairCreate(name="Chair 2", room_number="102", status=ChairStatus.ACTIVE),
    )
    assert created.name == "Chair 2"

    fetched = await repo.get(clinic_id, c.id)
    assert fetched == c

    by_name = await repo.get_by_name(clinic_id, "Chair 1")
    assert by_name == c

    all_chairs = await repo.list(clinic_id, include_inactive=True)
    assert len(all_chairs) == 1

    updated = await repo.update(c, ChairUpdate(notes="Service completed"))
    assert updated.notes == "Service completed"
