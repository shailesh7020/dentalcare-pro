from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest

from app.api.v1.hr import (
    assess_ai_burnout_risks,
    audit_ai_schedule_conflicts,
    audit_ai_training_compliance,
    clock_in,
    clock_out,
    create_employee,
    create_employee_document,
    create_interview_schedule,
    create_job_applicant,
    create_job_opening,
    create_work_shift,
    detect_ai_leave_conflicts,
    generate_payroll_run,
    get_ai_staffing_recommendations,
    get_employee,
    get_hr_dashboard,
    get_my_profile,
    list_attendance,
    list_employees,
    list_payroll_runs,
    list_payslips_for_employee,
    list_payslips_for_run,
    list_schedules,
    list_work_shifts,
    process_leave_action,
    schedule_staff,
    submit_leave_request,
    submit_performance_review,
    update_employee,
)
from app.models.appointment import Appointment, Chair
from app.models.hr import (
    AttendanceRecord,
    DocumentType,
    Employee,
    EmployeeDocument,
    EmployeeIncentive,
    EmployeeStatus,
    EmployeeTrainingRecord,
    EmploymentType,
    InterviewSchedule,
    JobApplicant,
    JobOpening,
    LeaveAllocation,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    PayrollRun,
    Payslip,
    PerformanceReview,
    StaffSchedule,
    TrainingCourse,
    WorkShift,
)
from app.schemas.hr import (
    ClockInRequest,
    ClockOutRequest,
    EmployeeCreate,
    EmployeeDocumentCreate,
    EmployeeUpdate,
    InterviewScheduleCreate,
    JobApplicantCreate,
    JobOpeningCreate,
    LeaveActionRequest,
    LeaveRequestCreate,
    PayrollRunCreate,
    PerformanceReviewCreate,
    StaffScheduleCreate,
    WorkShiftCreate,
)


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
        if "from chairs" in stmt:
            matches = [it for it in self.items if isinstance(it, Chair)]
            return FakeScalarResult(matches)
        if "from appointments" in stmt:
            matches = [it for it in self.items if isinstance(it, Appointment)]
            return FakeScalarResult(matches)
        if "from employees" in stmt:
            matches = [it for it in self.items if isinstance(it, Employee)]
            return FakeScalarResult(matches)
        if "from work_shifts" in stmt:
            matches = [it for it in self.items if isinstance(it, WorkShift)]
            return FakeScalarResult(matches)
        if "from staff_schedules" in stmt and "join employees" in stmt:
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
        if "from leave_requests" in stmt and "join employees" in stmt:
            reqs = [it for it in self.items if isinstance(it, LeaveRequest)]
            joined = []
            for r in reqs:
                emp = next((e for e in self.items if isinstance(e, Employee) and e.id == r.employee_id), None)
                if emp:
                    joined.append((r, emp))
            return FakeScalarResult(joined)
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
        if "from employee_training_records" in stmt and "join employees" in stmt:
            recs = [it for it in self.items if isinstance(it, EmployeeTrainingRecord)]
            joined = []
            for r in recs:
                emp = next((e for e in self.items if isinstance(e, Employee) and e.id == r.employee_id), None)
                if emp:
                    joined.append((r, emp))
            return FakeScalarResult(joined)
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
async def test_api_dashboard_and_employees():
    db = FakeDb()

    # 1. Dashboard metrics
    dash = await get_hr_dashboard(db=db)  # type: ignore
    assert hasattr(dash, "total_headcount")

    # 2. Create employee
    user_id = uuid4()
    emp_create = EmployeeCreate(
        employee_code="EMP-701",
        first_name="Dr. Vikram",
        last_name="Seth",
        email="vikram.seth@example.com",
        designation="Oral Surgeon",
        joining_date=date(2026, 1, 10),
        user_id=user_id,
        base_salary=120000.0,
    )
    emp_res = await create_employee(emp_create, db=db)  # type: ignore
    assert emp_res.id is not None
    assert emp_res.first_name == "Dr. Vikram"

    # 3. List employees
    all_emps = await list_employees(skip=0, limit=50, db=db)  # type: ignore
    assert len(all_emps) == 1

    # 4. Get employee
    single = await get_employee(emp_res.id, db=db)  # type: ignore
    assert single.id == emp_res.id

    # 5. Update employee
    updated = await update_employee(emp_res.id, EmployeeUpdate(phone="+919876543210"), db=db)  # type: ignore
    assert updated.phone == "+919876543210"

    # 6. ESS get my profile
    my_prof = await get_my_profile(user_id=user_id, db=db)  # type: ignore
    assert my_prof.id == emp_res.id


@pytest.mark.asyncio
async def test_api_shifts_and_schedules():
    db = FakeDb()

    clinic_id = uuid4()
    emp_id = uuid4()

    # 1. Create shift
    shift = await create_work_shift(
        WorkShiftCreate(
            name="General Morning",
            code="GEN-MORN",
            start_time=time(9, 0),
            end_time=time(14, 0),
            break_minutes=30,
        ),
        db=db,  # type: ignore
    )
    assert shift.id is not None

    shifts = await list_work_shifts(db=db)  # type: ignore
    assert len(shifts) == 1

    # 2. Schedule staff
    sched = await schedule_staff(
        StaffScheduleCreate(
            clinic_id=clinic_id,
            employee_id=emp_id,
            shift_id=shift.id,
            schedule_date=date(2026, 9, 14),
            start_time=time(9, 0),
            end_time=time(14, 0),
        ),
        db=db,  # type: ignore
    )
    assert sched.id is not None

    schedules = await list_schedules(clinic_id, date(2026, 9, 1), date(2026, 9, 30), db=db)  # type: ignore
    assert len(schedules) == 1


@pytest.mark.asyncio
async def test_api_attendance_and_leaves():
    db = FakeDb()

    clinic_id = uuid4()
    emp_id = uuid4()

    # 1. Clock in
    att = await clock_in(ClockInRequest(clinic_id=clinic_id, employee_id=emp_id), db=db)  # type: ignore
    assert att.check_in_time is not None

    # 2. Clock out
    att_out = await clock_out(employee_id=emp_id, payload=ClockOutRequest(notes="Done for the day"), db=db)  # type: ignore
    assert att_out.check_out_time is not None

    # 3. List attendance
    records = await list_attendance(clinic_id=clinic_id, record_date=datetime.now(UTC).date(), db=db)  # type: ignore
    assert len(records) == 1

    # 4. Leave request
    leave_req = await submit_leave_request(
        LeaveRequestCreate(
            clinic_id=clinic_id,
            employee_id=emp_id,
            leave_type=LeaveType.CASUAL,
            start_date=date(2026, 9, 25),
            end_date=date(2026, 9, 26),
            days_count=2.0,
            reason="Family event",
        ),
        db=db,  # type: ignore
    )
    assert leave_req.id is not None
    assert leave_req.status == LeaveStatus.SUBMITTED

    # 5. Review action
    reviewed = await process_leave_action(
        leave_req.id,
        LeaveActionRequest(action="HR_APPROVE", notes="Approved"),
        db=db,  # type: ignore
    )
    assert reviewed.status == LeaveStatus.HR_APPROVED


@pytest.mark.asyncio
async def test_api_payroll_and_recruitment():
    db = FakeDb()

    clinic_id = uuid4()
    emp = Employee(
        clinic_id=clinic_id,
        employee_code="EMP-801",
        first_name="Dr. Sameer",
        last_name="Khan",
        email="sameer.khan@example.com",
        designation="Periodontist",
        joining_date=date(2026, 1, 1),
        base_salary=85000.0,
        status=EmployeeStatus.ACTIVE,
    )
    db.add(emp)

    # 1. Generate payroll run
    payroll_run = await generate_payroll_run(
        PayrollRunCreate(clinic_id=clinic_id, period_month=9, period_year=2026),
        db=db,  # type: ignore
    )
    assert payroll_run.id is not None

    # 2. List payroll runs & payslips
    runs = await list_payroll_runs(clinic_id=clinic_id, db=db)  # type: ignore
    assert len(runs) == 1

    payslips = await list_payslips_for_run(payroll_run.id, db=db)  # type: ignore
    assert len(payslips) == 1

    emp_payslips = await list_payslips_for_employee(emp.id, db=db)  # type: ignore
    assert len(emp_payslips) == 1

    # 3. Recruitment opening & applicant
    job = await create_job_opening(
        JobOpeningCreate(
            clinic_id=clinic_id,
            title="Senior Dental Hygienist",
            employment_type=EmploymentType.FULL_TIME,
            open_positions=1,
            description="Perform prophylaxis and scaling.",
        ),
        db=db,  # type: ignore
    )
    assert job.id is not None

    applicant = await create_job_applicant(
        JobApplicantCreate(
            job_opening_id=job.id,
            full_name="Deepa Nair",
            email="deepa@example.com",
            phone="+919123456780",
        ),
        db=db,  # type: ignore
    )
    assert applicant.id is not None

    interview = await create_interview_schedule(
        InterviewScheduleCreate(
            applicant_id=applicant.id,
            scheduled_at=datetime(2026, 9, 20, 10, 0, tzinfo=UTC),
        ),
        db=db,  # type: ignore
    )
    assert interview.id is not None

    # 4. Performance review
    rev = await submit_performance_review(
        PerformanceReviewCreate(
            clinic_id=clinic_id,
            employee_id=emp.id,
            review_period="2026-Q3",
            clinical_skills_rating=4.8,
            patient_satisfaction_rating=4.9,
            punctuality_rating=4.5,
            teamwork_rating=4.7,
            protocol_adherence_rating=5.0,
        ),
        db=db,  # type: ignore
    )
    assert rev.id is not None
    assert rev.overall_rating >= 4.5

    # 5. Employee document
    doc = await create_employee_document(
        EmployeeDocumentCreate(
            employee_id=emp.id,
            document_type=DocumentType.DENTAL_LICENSE,
            title="State Dental Council Certificate",
            file_url="https://dentalcare-pro.internal/docs/license-801.pdf",
        ),
        db=db,  # type: ignore
    )
    assert doc.id is not None


@pytest.mark.asyncio
async def test_api_ai_workforce_endpoints():
    db = FakeDb()

    clinic_id = uuid4()
    # Add chairs
    for i in range(2):
        db.add(Chair(clinic_id=clinic_id, name=f"Chair {i+1}", is_active=True))

    today = date(2026, 9, 10)

    # 1. Staffing recommendations
    staffing = await get_ai_staffing_recommendations(clinic_id=clinic_id, target_date=today, db=db)  # type: ignore
    assert staffing.total_slots_analyzed == 2

    # 2. Schedule conflicts
    conflicts = await audit_ai_schedule_conflicts(clinic_id=clinic_id, start_date=today, end_date=today, db=db)  # type: ignore
    assert hasattr(conflicts, "total_conflicts")

    # 3. Leave conflicts
    leave_conflicts = await detect_ai_leave_conflicts(clinic_id=clinic_id, start_date=today, end_date=today, db=db)  # type: ignore
    assert hasattr(leave_conflicts, "conflicts_detected")

    # 4. Burnout risks
    burnout = await assess_ai_burnout_risks(clinic_id=clinic_id, db=db)  # type: ignore
    assert hasattr(burnout, "high_risk_count")

    # 5. Training compliance
    compliance = await audit_ai_training_compliance(clinic_id=clinic_id, db=db)  # type: ignore
    assert hasattr(compliance, "total_compliance_alerts")
