from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest

from app.models.hr import (
    ApplicantStage,
    AttendanceMethod,
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    EmployeeDocument,
    EmployeeIncentive,
    EmployeeStatus,
    EmployeeTrainingRecord,
    EmploymentType,
    InterviewSchedule,
    JobApplicant,
    JobOpening,
    JobStatus,
    LeaveAllocation,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    PayrollRun,
    PayrollStatus,
    Payslip,
    PayslipStatus,
    PerformanceReview,
    ScheduleStatus,
    ShiftType,
    StaffSchedule,
    TrainingCourse,
    WorkShift,
)
from app.repositories.hr_repository import HRRepository


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items) if items is not None else []

    def all(self):
        return self._items

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar_one(self):
        return self._items[0] if self._items else 0

    def scalar(self):
        return self._items[0] if self._items else 0

    def one(self):
        class Row:
            def __init__(self, total=0, active=0, on_leave=0, present=0, late=0):
                self.total = total
                self.active = active
                self.on_leave = on_leave
                self.present = present
                self.late = late
        return Row(total=len(self._items), active=len(self._items), present=len(self._items))


class FakeDb:
    def __init__(self):
        self.items = []
        self.deleted = []

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

    async def commit(self):
        pass

    async def refresh(self, item):
        pass

    async def execute(self, query):
        stmt = str(query).lower()
        if "from employees" in stmt:
            matches = [it for it in self.items if isinstance(it, Employee)]
            return FakeScalarResult(matches)
        if "from work_shifts" in stmt:
            matches = [it for it in self.items if isinstance(it, WorkShift)]
            return FakeScalarResult(matches)
        if "from staff_schedules" in stmt:
            matches = [it for it in self.items if isinstance(it, StaffSchedule)]
            return FakeScalarResult(matches)
        if "from attendance_records" in stmt:
            matches = [it for it in self.items if isinstance(it, AttendanceRecord)]
            return FakeScalarResult(matches)
        if "from leave_allocations" in stmt:
            matches = [it for it in self.items if isinstance(it, LeaveAllocation)]
            return FakeScalarResult(matches)
        if "from leave_requests" in stmt:
            matches = [it for it in self.items if isinstance(it, LeaveRequest)]
            return FakeScalarResult(matches)
        if "from payroll_runs" in stmt:
            matches = [it for it in self.items if isinstance(it, PayrollRun)]
            return FakeScalarResult(matches)
        if "from payslips" in stmt:
            matches = [it for it in self.items if isinstance(it, Payslip)]
            return FakeScalarResult(matches)
        if "from employee_incentives" in stmt:
            matches = [it for it in self.items if isinstance(it, EmployeeIncentive)]
            return FakeScalarResult(matches)
        if "from performance_reviews" in stmt:
            matches = [it for it in self.items if isinstance(it, PerformanceReview)]
            return FakeScalarResult(matches)
        if "from training_courses" in stmt:
            matches = [it for it in self.items if isinstance(it, TrainingCourse)]
            return FakeScalarResult(matches)
        if "from employee_training_records" in stmt:
            matches = [it for it in self.items if isinstance(it, EmployeeTrainingRecord)]
            return FakeScalarResult(matches)
        if "from job_openings" in stmt:
            matches = [it for it in self.items if isinstance(it, JobOpening)]
            return FakeScalarResult(matches)
        if "from job_applicants" in stmt:
            matches = [it for it in self.items if isinstance(it, JobApplicant)]
            return FakeScalarResult(matches)
        if "from interview_schedules" in stmt:
            matches = [it for it in self.items if isinstance(it, InterviewSchedule)]
            return FakeScalarResult(matches)
        if "from employee_documents" in stmt:
            matches = [it for it in self.items if isinstance(it, EmployeeDocument)]
            return FakeScalarResult(matches)
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_employee_crud_and_query():
    db = FakeDb()
    repo = HRRepository(db)  # type: ignore

    emp = await repo.create_employee(
        {
            "employee_code": "EMP-001",
            "first_name": "Aarav",
            "last_name": "Sharma",
            "email": "aarav.sharma@example.com",
            "designation": "Associate Dentist",
            "joining_date": date(2026, 1, 15),
            "base_salary": 75000.0,
            "status": EmployeeStatus.ACTIVE,
        }
    )
    assert emp.id is not None
    assert emp.employee_code == "EMP-001"

    fetched = await repo.get_employee_by_id(emp.id)
    assert fetched is not None

    by_code = await repo.get_employee_by_code("EMP-001")
    assert by_code is not None

    employees = await repo.list_employees()
    assert len(employees) == 1

    updated = await repo.update_employee(emp.id, {"designation": "Senior Endodontist"})
    assert updated is not None
    assert updated.designation == "Senior Endodontist"


@pytest.mark.asyncio
async def test_work_shifts_and_schedules():
    db = FakeDb()
    repo = HRRepository(db)  # type: ignore

    shift = await repo.create_work_shift(
        {
            "name": "Morning General",
            "code": "MORN",
            "start_time": time(9, 0),
            "end_time": time(14, 0),
            "break_minutes": 30,
            "shift_type": ShiftType.REGULAR,
        }
    )
    assert shift.id is not None
    assert shift.code == "MORN"

    shifts = await repo.list_work_shifts()
    assert len(shifts) == 1

    emp_id = uuid4()
    clinic_id = uuid4()
    schedule = await repo.create_staff_schedule(
        {
            "clinic_id": clinic_id,
            "employee_id": emp_id,
            "shift_id": shift.id,
            "schedule_date": date(2026, 9, 10),
            "start_time": time(9, 0),
            "end_time": time(14, 0),
            "status": ScheduleStatus.SCHEDULED,
        }
    )
    assert schedule.id is not None
    assert schedule.status == ScheduleStatus.SCHEDULED

    schedules = await repo.list_staff_schedules(clinic_id, date(2026, 9, 1), date(2026, 9, 30))
    assert len(schedules) == 1


@pytest.mark.asyncio
async def test_attendance_and_leaves():
    db = FakeDb()
    repo = HRRepository(db)  # type: ignore

    emp_id = uuid4()
    clinic_id = uuid4()
    today = date(2026, 9, 9)

    att = await repo.create_attendance_record(
        {
            "clinic_id": clinic_id,
            "employee_id": emp_id,
            "date": today,
            "check_in_time": datetime(2026, 9, 9, 9, 5, tzinfo=UTC),
            "entry_method": AttendanceMethod.QR_CODE,
            "status": AttendanceStatus.PRESENT,
        }
    )
    assert att.id is not None

    fetched_att = await repo.get_attendance_record(emp_id, today)
    assert fetched_att is not None
    assert fetched_att.entry_method == AttendanceMethod.QR_CODE

    # Leave allocation & request
    alloc = await repo.get_or_create_leave_allocation(emp_id, 2026, LeaveType.CASUAL, 12.0)
    assert alloc.total_days == 12.0

    leave_req = await repo.create_leave_request(
        {
            "clinic_id": clinic_id,
            "employee_id": emp_id,
            "leave_type": LeaveType.CASUAL,
            "start_date": date(2026, 9, 15),
            "end_date": date(2026, 9, 16),
            "days_count": 2.0,
            "reason": "Family function",
            "status": LeaveStatus.SUBMITTED,
        }
    )
    assert leave_req.id is not None
    assert leave_req.days_count == 2.0


@pytest.mark.asyncio
async def test_payroll_runs_and_recruitment():
    db = FakeDb()
    repo = HRRepository(db)  # type: ignore

    emp_id = uuid4()
    clinic_id = uuid4()

    run = await repo.create_payroll_run(
        {
            "clinic_id": clinic_id,
            "run_number": "PR-2026-09-001",
            "period_month": 9,
            "period_year": 2026,
            "status": PayrollStatus.DRAFT,
            "total_gross": 105000.0,
            "total_deductions": 12500.0,
            "total_net": 92500.0,
            "total_employees": 1,
        }
    )
    assert run.id is not None

    payslip = await repo.create_payslip(
        {
            "payroll_run_id": run.id,
            "employee_id": emp_id,
            "clinic_id": clinic_id,
            "period_month": 9,
            "period_year": 2026,
            "basic_salary": 75000.0,
            "gross_earnings": 105000.0,
            "total_deductions": 12500.0,
            "net_salary": 92500.0,
            "status": PayslipStatus.GENERATED,
        }
    )
    assert payslip.id is not None
    assert payslip.net_salary == 92500.0

    # Recruitment
    opening = await repo.create_job_opening(
        {
            "title": "Chairside Dental Assistant",
            "employment_type": EmploymentType.FULL_TIME,
            "open_positions": 2,
            "status": JobStatus.OPEN,
            "description": "Assist endodontists with surgical setups.",
        }
    )
    assert opening.id is not None

    applicant = await repo.create_job_applicant(
        {
            "job_opening_id": opening.id,
            "full_name": "Priya Nair",
            "email": "priya.nair@example.com",
            "phone": "+919876543210",
            "current_stage": ApplicantStage.APPLIED,
        }
    )
    assert applicant.id is not None

    # Dashboard metrics
    metrics = await repo.get_hr_dashboard_metrics(clinic_id=clinic_id)
    assert "total_headcount" in metrics
    assert "attendance_rate" in metrics
