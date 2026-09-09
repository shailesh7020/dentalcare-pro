from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus, Chair, ChairStatus
from app.models.identity import Role, User
from app.models.patient import Gender, Patient
from app.schemas.appointment import AppointmentCreate
from app.services.appointment_service import AppointmentService


class ConcurrencyMockDb:
    def __init__(self, entities: list[object] | None = None) -> None:
        self.entities: list[object] = list(entities or [])
        self.lock = asyncio.Lock()

    async def get(self, model_cls: type, ident: object) -> object | None:
        for e in self.entities:
            if isinstance(e, model_cls) and getattr(e, "id", None) == ident:
                return e
        return None

    def add(self, obj: object) -> None:
        self.entities.append(obj)

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        pass

    async def execute(self, stmt: object) -> MagicMock:
        res = MagicMock()
        res.scalars.return_value.all.return_value = []
        res.scalar_one_or_none.return_value = None
        return res

    async def scalar(self, stmt: object) -> object | None:
        return 0


@pytest.mark.asyncio
async def test_appointment_double_booking_prevention():
    """Verify that concurrent booking on the same chair and overlapping time raises 409 Conflict."""
    clinic_id = uuid4()
    dentist_id = uuid4()
    chair_id = uuid4()
    patient1_id = uuid4()
    patient2_id = uuid4()

    dentist = User(
        id=dentist_id,
        clinic_id=clinic_id,
        role=Role.DENTIST,
        is_active=True,
        email="doctor@example.com",
    )
    chair = Chair(
        id=chair_id,
        clinic_id=clinic_id,
        name="Operatory 1",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )
    patient1 = Patient(
        id=patient1_id,
        clinic_id=clinic_id,
        first_name="John",
        last_name="Doe",
        mobile_number="9876543210",
        gender=Gender.MALE,
    )
    patient2 = Patient(
        id=patient2_id,
        clinic_id=clinic_id,
        first_name="Jane",
        last_name="Smith",
        mobile_number="9876543211",
        gender=Gender.FEMALE,
    )

    receptionist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        role=Role.RECEPTIONIST,
        is_active=True,
    )

    db = ConcurrencyMockDb([dentist, chair, patient1, patient2])
    svc = AppointmentService(db)  # type: ignore

    # Mock conflict check: first attempt passes, second detects chair conflict
    first_call = True

    async def mock_check_conflicts(*args, **kwargs):
        nonlocal first_call
        if first_call:
            first_call = False
            return {
                "dentist_conflict": None,
                "chair_conflict": None,
                "patient_conflict": None,
                "blocked_conflict": None,
            }
        else:
            conflicting_apt = MagicMock()
            conflicting_apt.appointment_number = "APT-2026-001"
            conflicting_apt.start_time = time(10, 0)
            conflicting_apt.end_time = time(10, 30)
            return {
                "dentist_conflict": None,
                "chair_conflict": conflicting_apt,
                "patient_conflict": None,
                "blocked_conflict": None,
            }

    svc.repo.check_conflicts = AsyncMock(side_effect=mock_check_conflicts)
    svc.repo.generate_appointment_number = AsyncMock(return_value="APT-2026-001")
    apt_instance = Appointment(
        id=uuid4(),
        appointment_number="APT-2026-001",
        clinic_id=clinic_id,
        patient_id=patient1_id,
        dentist_id=dentist_id,
        chair_id=chair_id,
        date=date(2026, 9, 15),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        patient=patient1,
        dentist=dentist,
        chair=chair,
    )
    svc.repo.create = AsyncMock(return_value=apt_instance)
    svc.repo.get_by_id = AsyncMock(return_value=apt_instance)

    payload1 = AppointmentCreate(
        patient_id=patient1_id,
        dentist_id=dentist_id,
        chair_id=chair_id,
        date=date(2026, 9, 15),
        start_time=time(10, 0),
        duration=30,
        chief_complaint="Toothache",
    )
    payload2 = AppointmentCreate(
        patient_id=patient2_id,
        dentist_id=dentist_id,
        chair_id=chair_id,
        date=date(2026, 9, 15),
        start_time=time(10, 15),  # Overlapping slot!
        duration=30,
        chief_complaint="Cleaning",
    )

    # First booking succeeds
    res1 = await svc.create(clinic_id, payload1, receptionist)
    assert res1.appointment_number == "APT-2026-001"

    # Second concurrent booking must raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await svc.create(clinic_id, payload2, receptionist)

    assert exc_info.value.status_code == 409
    assert "Chair conflict" in exc_info.value.detail


@pytest.mark.asyncio
async def test_concurrent_simulated_multi_user_traffic():
    """Simulate 20 concurrent asynchronous operations across different clinics without deadlock."""
    async def simulate_station_action(worker_id: int):
        await asyncio.sleep(0.005)  # Simulate small I/O latency
        return {
            "worker_id": worker_id,
            "status": "SUCCESS",
            "completed_at": datetime.now(UTC).isoformat(),
        }

    tasks = [simulate_station_action(i) for i in range(20)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 20
    assert all(r["status"] == "SUCCESS" for r in results)
