from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest

from app.models.appointment import Appointment, Chair
from app.models.hr import (
    AttendanceRecord,
    Employee,
    EmployeeStatus,
    EmployeeTrainingRecord,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    ScheduleStatus,
    StaffSchedule,
)
from app.services.ai.workforce_ai_service import WorkforceAIService


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items) if items is not None else []

    def all(self):
        return self._items

    def scalars(self):
        return self


class FakeDb:
    def __init__(self):
        self.items = []

    def add(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = uuid4()
        if not hasattr(item, "created_at") or item.created_at is None:
            item.created_at = datetime.now(UTC)
        if not hasattr(item, "updated_at") or item.updated_at is None:
            item.updated_at = datetime.now(UTC)
        if not hasattr(item, "deleted_at"):
            item.deleted_at = None
        self.items.append(item)

    async def execute(self, query):
        stmt = str(query).lower()
        if "from chairs" in stmt:
            matches = [it for it in self.items if isinstance(it, Chair)]
            return FakeScalarResult(matches)
        if "from appointments" in stmt:
            matches = [it for it in self.items if isinstance(it, Appointment)]
            return FakeScalarResult(matches)
        if "from staff_schedules" in stmt and "join employees" in stmt:
            # Join result
            scheds = [it for it in self.items if isinstance(it, StaffSchedule)]
            joined = []
            for s in scheds:
                emp = next((e for e in self.items if isinstance(e, Employee) and e.id == s.employee_id), None)
                if emp:
                    joined.append((s, emp))
            return FakeScalarResult(joined)
        if "from staff_schedules" in stmt:
            matches = [it for it in self.items if isinstance(it, StaffSchedule)]
            return FakeScalarResult(matches)
        if "from employees" in stmt:
            matches = [it for it in self.items if isinstance(it, Employee)]
            return FakeScalarResult(matches)
        if "from attendance_records" in stmt:
            matches = [it for it in self.items if isinstance(it, AttendanceRecord)]
            return FakeScalarResult(matches)
        if "from leave_requests" in stmt:
            reqs = [it for it in self.items if isinstance(it, LeaveRequest)]
            joined = []
            for r in reqs:
                emp = next((e for e in self.items if isinstance(e, Employee) and e.id == r.employee_id), None)
                if emp:
                    joined.append((r, emp))
            return FakeScalarResult(joined)
        if "from employee_training_records" in stmt:
            recs = [it for it in self.items if isinstance(it, EmployeeTrainingRecord)]
            joined = []
            for r in recs:
                emp = next((e for e in self.items if isinstance(e, Employee) and e.id == r.employee_id), None)
                if emp:
                    joined.append((r, emp))
            return FakeScalarResult(joined)
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_ai_staffing_recommendations():
    db = FakeDb()
    ai = WorkforceAIService(db)  # type: ignore

    clinic_id = uuid4()
    # 3 active chairs
    for i in range(3):
        db.add(Chair(clinic_id=clinic_id, name=f"Chair {i+1}", is_active=True))

    target_date = date(2026, 9, 15)
    # 5 morning appointments
    for i in range(5):
        db.add(
            Appointment(
                clinic_id=clinic_id,
                patient_id=uuid4(),
                dentist_id=uuid4(),
                chair_id=uuid4(),
                appointment_number=f"APT-{i}",
                date=target_date,
                start_time=time(9 + (i % 3), 0),
                end_time=time(10 + (i % 3), 0),
            )
        )

    # 1 clinician scheduled in morning
    emp_id = uuid4()
    db.add(
        StaffSchedule(
            clinic_id=clinic_id,
            employee_id=emp_id,
            schedule_date=target_date,
            start_time=time(9, 0),
            end_time=time(13, 0),
            status=ScheduleStatus.SCHEDULED,
        )
    )

    res = await ai.get_staffing_recommendations(clinic_id, target_date)
    assert res.total_slots_analyzed == 2
    assert len(res.recommendations) == 2
    morn = next(r for r in res.recommendations if "Morning" in r.time_slot)
    assert morn.appointments_booked == 5


@pytest.mark.asyncio
async def test_ai_schedule_conflict_auditor():
    db = FakeDb()
    ai = WorkforceAIService(db)  # type: ignore

    clinic_id = uuid4()
    emp = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-301",
        first_name="Dr. Anita",
        last_name="Desai",
        email="anita.desai@example.com",
        designation="General Dentist",
        joining_date=date(2026, 1, 1),
    )
    db.add(emp)

    # 7 consecutive working days
    for day in range(1, 8):
        db.add(
            StaffSchedule(
                clinic_id=clinic_id,
                employee_id=emp.id,
                schedule_date=date(2026, 9, day),
                start_time=time(9, 0),
                end_time=time(17, 0),
                status=ScheduleStatus.SCHEDULED,
            )
        )

    conflicts = await ai.audit_schedule_conflicts(clinic_id, date(2026, 9, 1), date(2026, 9, 10))
    assert conflicts.total_conflicts >= 1
    assert any(c.conflict_type == "CONSECUTIVE_WORK_DAYS" for c in conflicts.conflicts)


@pytest.mark.asyncio
async def test_ai_leave_conflict_detection():
    db = FakeDb()
    ai = WorkforceAIService(db)  # type: ignore

    clinic_id = uuid4()
    # 2 endodontists
    emp1 = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-401",
        first_name="Dr. Sanjay",
        last_name="Gupta",
        email="sanjay@example.com",
        designation="Endodontist",
        specialization="Endodontics",
        joining_date=date(2026, 1, 1),
    )
    emp2 = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-402",
        first_name="Dr. Sneha",
        last_name="Patel",
        email="sneha@example.com",
        designation="Endodontist",
        specialization="Endodontics",
        joining_date=date(2026, 1, 1),
    )
    db.add(emp1)
    db.add(emp2)

    # Both apply for leave in same window
    db.add(
        LeaveRequest(
            clinic_id=clinic_id,
            employee_id=emp1.id,
            leave_type=LeaveType.ANNUAL,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 25),
            status=LeaveStatus.SUBMITTED,
            reason="Vacation",
        )
    )
    db.add(
        LeaveRequest(
            clinic_id=clinic_id,
            employee_id=emp2.id,
            leave_type=LeaveType.CASUAL,
            start_date=date(2026, 9, 22),
            end_date=date(2026, 9, 24),
            status=LeaveStatus.SUBMITTED,
            reason="Conference",
        )
    )

    conflicts = await ai.detect_leave_conflicts(clinic_id, date(2026, 9, 20), date(2026, 9, 25))
    assert conflicts.conflicts_detected >= 1
    assert "Endodontics" in conflicts.details[0].department_name


@pytest.mark.asyncio
async def test_ai_burnout_risk_assessment():
    db = FakeDb()
    ai = WorkforceAIService(db)  # type: ignore

    clinic_id = uuid4()
    emp = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-501",
        first_name="Dr. Vivek",
        last_name="Malhotra",
        email="vivek@example.com",
        designation="Oral Surgeon",
        joining_date=date(2026, 1, 1),
        status=EmployeeStatus.ACTIVE,
    )
    db.add(emp)

    # Heavy overtime accumulated
    for day in range(1, 20):
        db.add(
            AttendanceRecord(
                clinic_id=clinic_id,
                employee_id=emp.id,
                date=date(2026, 8, day),
                overtime_minutes=120,  # 2 hrs per day * 20 = 40 hrs
            )
        )

    res = await ai.assess_burnout_risks(clinic_id)
    assert len(res.assessments) == 1
    surgeon = res.assessments[0]
    assert surgeon.overtime_hours_month >= 25.0
    assert surgeon.risk_level == "HIGH"


@pytest.mark.asyncio
async def test_ai_training_compliance_auditor():
    db = FakeDb()
    ai = WorkforceAIService(db)  # type: ignore

    clinic_id = uuid4()
    # Employee with license expiring in 15 days
    today = datetime.now(UTC).date()
    exp_date = date.fromordinal(today.toordinal() + 15)
    emp = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-601",
        first_name="Dr. Meera",
        last_name="Joshi",
        email="meera@example.com",
        designation="Pedodontist",
        license_number="DCI-99824",
        license_expiry_date=exp_date,
        joining_date=date(2026, 1, 1),
    )
    db.add(emp)

    res = await ai.audit_training_compliance(clinic_id)
    assert res.total_compliance_alerts >= 1
    assert any("License" in a.title for a in res.alerts)
