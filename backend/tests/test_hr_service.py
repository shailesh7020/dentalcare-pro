from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.hr import (
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    EmployeeIncentive,
    EmployeeStatus,
    IncentiveCriterion,
    IncentiveStatus,
    LeaveAllocation,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    PayrollRun,
    Payslip,
    PerformanceReview,
    StaffSchedule,
    WorkShift,
)
from app.schemas.hr import (
    EmployeeCreate,
    LeaveActionRequest,
    LeaveRequestCreate,
    PayrollRunCreate,
    PerformanceReviewCreate,
    StaffScheduleCreate,
)
from app.services.hr_service import HRService


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
            params = query.compile().params if hasattr(query, "compile") else {}
            target_type = None
            for k, v in params.items():
                if "leave_type" in k:
                    target_type = v
                    break
            if target_type:
                matches = [it for it in matches if it.leave_type == target_type]
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
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_employee_onboarding_and_leave_balance_init():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    emp_data = EmployeeCreate(
        employee_code="EMP-101",
        first_name="Dr. Rohan",
        last_name="Verma",
        email="rohan.verma@example.com",
        designation="Lead Prosthodontist",
        joining_date=date(2026, 3, 1),
        base_salary=90000.0,
    )
    employee = await service.create_employee(emp_data)
    assert employee.id is not None
    assert employee.first_name == "Dr. Rohan"

    # Verify default allocations were initialized
    allocs = [it for it in db.items if isinstance(it, LeaveAllocation) and it.employee_id == employee.id]
    assert len(allocs) == 4
    casual = next(a for a in allocs if a.leave_type == LeaveType.CASUAL)
    assert casual.total_days == 12.0


@pytest.mark.asyncio
async def test_schedule_conflict_prevention():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    emp_id = uuid4()
    clinic_id = uuid4()

    # First valid schedule
    sched1 = await service.schedule_staff(
        StaffScheduleCreate(
            clinic_id=clinic_id,
            employee_id=emp_id,
            schedule_date=date(2026, 9, 12),
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
    )
    assert sched1.id is not None

    # Overlapping schedule should raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await service.schedule_staff(
            StaffScheduleCreate(
                clinic_id=clinic_id,
                employee_id=emp_id,
                schedule_date=date(2026, 9, 12),
                start_time=time(11, 0),
                end_time=time(15, 0),
            )
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_attendance_clock_in_out_and_overtime():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    emp_id = uuid4()
    clinic_id = uuid4()

    # Clock in
    att = await service.clock_in(clinic_id=clinic_id, employee_id=emp_id)
    assert att.check_in_time is not None
    assert att.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]

    # Double clock-in should fail
    with pytest.raises(HTTPException) as exc_info:
        await service.clock_in(clinic_id=clinic_id, employee_id=emp_id)
    assert exc_info.value.status_code == 400

    # Clock out
    att_out = await service.clock_out(employee_id=emp_id)
    assert att_out.check_out_time is not None


@pytest.mark.asyncio
async def test_two_tier_leave_workflow_approval_rejection():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    emp_id = uuid4()
    clinic_id = uuid4()

    # Setup leave allocation
    alloc = LeaveAllocation(
        employee_id=emp_id,
        year=2026,
        leave_type=LeaveType.CASUAL,
        total_days=10.0,
        used_days=0.0,
        pending_days=0.0,
    )
    db.add(alloc)

    # 1. Request leave
    req = await service.request_leave(
        LeaveRequestCreate(
            clinic_id=clinic_id,
            employee_id=emp_id,
            leave_type=LeaveType.CASUAL,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 21),
            days_count=2.0,
            reason="Medical recovery",
        )
    )
    assert req.status == LeaveStatus.SUBMITTED
    assert alloc.pending_days == 2.0

    # 2. Manager Review
    mgr_id = uuid4()
    req_mgr = await service.process_leave_action(
        req.id,
        mgr_id,
        LeaveActionRequest(action="MANAGER_APPROVE", notes="Approved by Clinic Manager"),
    )
    assert req_mgr.status == LeaveStatus.MANAGER_APPROVED

    # 3. HR Approval
    hr_id = uuid4()
    req_hr = await service.process_leave_action(
        req.id,
        hr_id,
        LeaveActionRequest(action="HR_APPROVE", notes="Approved by Central HR"),
    )
    assert req_hr.status == LeaveStatus.HR_APPROVED
    assert alloc.pending_days == 0.0
    assert alloc.used_days == 2.0


@pytest.mark.asyncio
async def test_automated_payroll_calculation_engine():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    clinic_id = uuid4()
    emp = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-202",
        first_name="Dr. Kavita",
        last_name="Rao",
        email="kavita.rao@example.com",
        designation="Consultant Orthodontist",
        joining_date=date(2026, 1, 1),
        base_salary=100000.0,
        status=EmployeeStatus.ACTIVE,
    )
    db.add(emp)

    # Approved Incentive
    inc = EmployeeIncentive(
        employee_id=emp.id,
        period_month=9,
        period_year=2026,
        criterion_type=IncentiveCriterion.TREATMENTS_COMPLETED,
        target_value=20.0,
        achieved_value=25.0,
        rate_or_percentage=500.0,
        calculated_amount=5000.0,
        status=IncentiveStatus.APPROVED,
    )
    db.add(inc)

    # Run payroll for September 2026
    payroll_run = await service.generate_payroll_run(
        PayrollRunCreate(clinic_id=clinic_id, period_month=9, period_year=2026)
    )
    assert payroll_run.total_employees == 1
    assert payroll_run.total_gross > 100000.0
    assert payroll_run.total_net > 0.0

    payslips = [it for it in db.items if isinstance(it, Payslip) and it.payroll_run_id == payroll_run.id]
    assert len(payslips) == 1
    ps = payslips[0]
    assert ps.basic_salary == 100000.0
    assert ps.hra_allowance == 40000.0
    assert ps.special_allowance == 10000.0
    assert ps.medical_allowance == 1500.0
    assert ps.incentive_amount == 5000.0
    assert ps.gross_earnings == 156500.0
    assert ps.pf_deduction == 1800.0
    assert ps.professional_tax == 200.0
    assert ps.net_salary == ps.gross_earnings - ps.total_deductions


@pytest.mark.asyncio
async def test_performance_review_weighted_rating():
    db = FakeDb()
    service = HRService(db)  # type: ignore

    clinic_id = uuid4()
    emp_id = uuid4()

    review = await service.create_performance_review(
        PerformanceReviewCreate(
            clinic_id=clinic_id,
            employee_id=emp_id,
            review_period="2026-Q3",
            clinical_skills_rating=5.0,
            patient_satisfaction_rating=4.5,
            punctuality_rating=4.0,
            teamwork_rating=4.5,
            protocol_adherence_rating=5.0,
        )
    )
    # 5.0*0.30 (1.5) + 4.5*0.25 (1.125) + 5.0*0.20 (1.0) + 4.5*0.15 (0.675) + 4.0*0.10 (0.4) = 4.7
    assert review.overall_rating == 4.7
