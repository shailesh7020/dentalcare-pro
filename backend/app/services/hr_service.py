from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import (
    ApplicantStage,
    AttendanceMethod,
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    EmployeeDocument,
    EmployeeStatus,
    EmployeeTrainingRecord,
    IncentiveStatus,
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
    StaffSchedule,
    TrainingCourse,
    WorkShift,
)
from app.repositories.hr_repository import HRRepository
from app.schemas.hr import (
    EmployeeCreate,
    EmployeeUpdate,
    LeaveActionRequest,
    LeaveRequestCreate,
    PayrollRunCreate,
    PerformanceReviewCreate,
    StaffScheduleCreate,
)


class HRService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HRRepository(db)

    # ---------------------------------------------------------
    # Employee Management
    # ---------------------------------------------------------
    async def create_employee(self, data: EmployeeCreate) -> Employee:
        # Verify unique employee_code
        existing = await self.repo.get_employee_by_code(data.employee_code, data.organization_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with code {data.employee_code} already exists.",
            )
        # Verify unique user_id if provided
        if data.user_id:
            existing_user_emp = await self.repo.get_employee_by_user_id(data.user_id)
            if existing_user_emp:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A profile for this user already exists.",
                )

        emp_dict = data.model_dump()
        employee = await self.repo.create_employee(emp_dict)

        # Initialize default leave allocations for the current year
        current_year = datetime.now(UTC).date().year
        default_leaves = [
            (LeaveType.CASUAL, 12.0),
            (LeaveType.SICK, 10.0),
            (LeaveType.ANNUAL, 15.0),
            (LeaveType.EMERGENCY, 5.0),
        ]
        for l_type, days in default_leaves:
            await self.repo.get_or_create_leave_allocation(employee.id, current_year, l_type, days)

        return employee

    async def get_employee(self, employee_id: UUID) -> Employee:
        emp = await self.repo.get_employee_by_id(employee_id)
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return emp

    async def update_employee(self, employee_id: UUID, updates: EmployeeUpdate) -> Employee:
        emp = await self.repo.update_employee(employee_id, updates.model_dump(exclude_unset=True))
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return emp

    async def list_employees(
        self,
        organization_id: UUID | None = None,
        clinic_id: UUID | None = None,
        department_id: UUID | None = None,
        status_filter: EmployeeStatus | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Employee]:
        return await self.repo.list_employees(
            organization_id=organization_id,
            clinic_id=clinic_id,
            department_id=department_id,
            status=status_filter,
            search=search,
            skip=skip,
            limit=limit,
        )

    # ---------------------------------------------------------
    # Work Shifts & Scheduling
    # ---------------------------------------------------------
    async def create_work_shift(self, data: dict) -> WorkShift:
        return await self.repo.create_work_shift(data)

    async def list_work_shifts(self, organization_id: UUID | None = None, clinic_id: UUID | None = None) -> list[WorkShift]:
        return await self.repo.list_work_shifts(organization_id, clinic_id)

    async def schedule_staff(self, data: StaffScheduleCreate) -> StaffSchedule:
        # Check for schedule conflicts
        has_conflict, conflict_type, msg = await self.repo.check_schedule_conflict(
            clinic_id=data.clinic_id,
            employee_id=data.employee_id,
            schedule_date=data.schedule_date,
            start_time=data.start_time,
            end_time=data.end_time,
            chair_id=data.chair_id,
        )
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scheduling Conflict ({conflict_type}): {msg}",
            )
        return await self.repo.create_staff_schedule(data.model_dump())

    async def list_schedules(
        self,
        clinic_id: UUID,
        start_date: date,
        end_date: date,
        employee_id: UUID | None = None,
    ) -> list[StaffSchedule]:
        return await self.repo.list_staff_schedules(clinic_id, start_date, end_date, employee_id)

    # ---------------------------------------------------------
    # Attendance Management
    # ---------------------------------------------------------
    async def clock_in(
        self,
        clinic_id: UUID,
        employee_id: UUID,
        entry_method: AttendanceMethod = AttendanceMethod.MANUAL,
        notes: str | None = None,
    ) -> AttendanceRecord:
        now = datetime.now(UTC)
        today = now.date()

        existing = await self.repo.get_attendance_record(employee_id, today)
        if existing and existing.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee has already clocked in today.",
            )

        # Check if late compared to scheduled shift start
        is_late = False
        late_minutes = 0
        schedules = await self.repo.list_staff_schedules(clinic_id, today, today, employee_id)
        if schedules:
            sched_start = schedules[0].start_time
            sched_dt = datetime.combine(today, sched_start, tzinfo=UTC)
            diff_minutes = int((now - sched_dt).total_seconds() / 60)
            if diff_minutes > 15:
                is_late = True
                late_minutes = diff_minutes

        if existing:
            updated = await self.repo.update_attendance_record(
                existing.id,
                {
                    "check_in_time": now,
                    "entry_method": entry_method,
                    "status": AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT,
                    "is_late": is_late,
                    "late_minutes": late_minutes,
                    "notes": notes,
                },
            )
            return updated  # type: ignore

        data = {
            "organization_id": None,
            "clinic_id": clinic_id,
            "employee_id": employee_id,
            "date": today,
            "check_in_time": now,
            "entry_method": entry_method,
            "status": AttendanceStatus.LATE if is_late else AttendanceStatus.PRESENT,
            "is_late": is_late,
            "late_minutes": late_minutes,
            "notes": notes,
        }
        return await self.repo.create_attendance_record(data)

    async def clock_out(self, employee_id: UUID, notes: str | None = None) -> AttendanceRecord:
        now = datetime.now(UTC)
        today = now.date()

        record = await self.repo.get_attendance_record(employee_id, today)
        if not record or not record.check_in_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot clock out without an active clock-in today.",
            )

        # Calculate overtime & early departure
        overtime_mins = 0
        is_early = False
        early_mins = 0

        # Duration worked
        duration_hrs = (now - record.check_in_time).total_seconds() / 3600
        if duration_hrs > 8.0:
            overtime_mins = int((duration_hrs - 8.0) * 60)

        schedules = await self.repo.list_staff_schedules(record.clinic_id, today, today, employee_id)
        if schedules:
            sched_end = schedules[0].end_time
            sched_end_dt = datetime.combine(today, sched_end, tzinfo=UTC)
            if now < sched_end_dt:
                diff_mins = int((sched_end_dt - now).total_seconds() / 60)
                if diff_mins > 15:
                    is_early = True
                    early_mins = diff_mins

        updated = await self.repo.update_attendance_record(
            record.id,
            {
                "check_out_time": now,
                "overtime_minutes": overtime_mins,
                "is_early_departure": is_early,
                "early_departure_minutes": early_mins,
                "notes": notes or record.notes,
            },
        )
        return updated  # type: ignore

    async def list_attendance(
        self, clinic_id: UUID, record_date: date, employee_id: UUID | None = None
    ) -> list[AttendanceRecord]:
        return await self.repo.list_attendance(clinic_id, record_date, employee_id)

    # ---------------------------------------------------------
    # Leave Management & Two-Tier Workflow
    # ---------------------------------------------------------
    async def request_leave(self, data: LeaveRequestCreate) -> LeaveRequest:
        # Check leave allocation balance
        year = data.start_date.year
        allocation = await self.repo.get_or_create_leave_allocation(data.employee_id, year, data.leave_type)
        available = allocation.total_days - (allocation.used_days + allocation.pending_days)
        if data.leave_type != LeaveType.UNPAID and data.days_count > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient leave balance. Available: {available} days, Requested: {data.days_count} days.",
            )

        # Create leave request with SUBMITTED status
        req_dict = data.model_dump()
        req_dict["status"] = LeaveStatus.SUBMITTED
        leave_req = await self.repo.create_leave_request(req_dict)

        # Update pending days in allocation
        if data.leave_type != LeaveType.UNPAID:
            allocation.pending_days += data.days_count
            await self.db.commit()

        return leave_req

    async def process_leave_action(
        self, request_id: UUID, reviewer_user_id: UUID, action_data: LeaveActionRequest
    ) -> LeaveRequest:
        leave_req = await self.repo.get_leave_request_by_id(request_id)
        if not leave_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

        now = datetime.now(UTC)
        year = leave_req.start_date.year
        allocation = await self.repo.get_or_create_leave_allocation(leave_req.employee_id, year, leave_req.leave_type)

        act = action_data.action.upper()
        if act == "MANAGER_APPROVE":
            leave_req.status = LeaveStatus.MANAGER_APPROVED
            leave_req.manager_id = reviewer_user_id
            leave_req.manager_notes = action_data.notes
            leave_req.manager_reviewed_at = now
        elif act == "MANAGER_REJECT":
            leave_req.status = LeaveStatus.REJECTED
            leave_req.manager_id = reviewer_user_id
            leave_req.manager_notes = action_data.notes
            leave_req.manager_reviewed_at = now
            if leave_req.leave_type != LeaveType.UNPAID:
                allocation.pending_days = max(0.0, allocation.pending_days - leave_req.days_count)
        elif act == "HR_APPROVE":
            leave_req.status = LeaveStatus.HR_APPROVED
            leave_req.hr_id = reviewer_user_id
            leave_req.hr_notes = action_data.notes
            leave_req.hr_reviewed_at = now
            if leave_req.leave_type != LeaveType.UNPAID:
                allocation.pending_days = max(0.0, allocation.pending_days - leave_req.days_count)
                allocation.used_days += leave_req.days_count
        elif act == "HR_REJECT":
            leave_req.status = LeaveStatus.REJECTED
            leave_req.hr_id = reviewer_user_id
            leave_req.hr_notes = action_data.notes
            leave_req.hr_reviewed_at = now
            if leave_req.leave_type != LeaveType.UNPAID:
                allocation.pending_days = max(0.0, allocation.pending_days - leave_req.days_count)
        elif act == "CANCEL":
            leave_req.status = LeaveStatus.CANCELLED
            if leave_req.leave_type != LeaveType.UNPAID:
                allocation.pending_days = max(0.0, allocation.pending_days - leave_req.days_count)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported leave action: {act}")

        await self.db.commit()
        await self.db.refresh(leave_req)
        return leave_req

    async def list_leave_requests(
        self, clinic_id: UUID | None = None, employee_id: UUID | None = None, status_filter: LeaveStatus | None = None
    ) -> list[LeaveRequest]:
        return await self.repo.list_leave_requests(clinic_id, employee_id, status_filter)

    async def get_leave_allocations(self, employee_id: UUID, year: int) -> list[LeaveAllocation]:
        return await self.repo.list_leave_allocations(employee_id, year)

    # ---------------------------------------------------------
    # Payroll Engine
    # ---------------------------------------------------------
    async def generate_payroll_run(self, data: PayrollRunCreate) -> PayrollRun:
        # 1. Fetch active employees
        employees = await self.repo.list_employees(
            organization_id=data.organization_id,
            clinic_id=data.clinic_id,
            status=EmployeeStatus.ACTIVE,
            limit=500,
        )

        run_number = f"PR-{data.period_year}-{data.period_month:02d}-{int(datetime.now(UTC).timestamp())}"
        payroll_run = await self.repo.create_payroll_run(
            {
                "organization_id": data.organization_id,
                "clinic_id": data.clinic_id,
                "run_number": run_number,
                "period_month": data.period_month,
                "period_year": data.period_year,
                "status": PayrollStatus.DRAFT,
                "notes": data.notes,
            }
        )

        total_gross = 0.0
        total_deductions = 0.0
        total_net = 0.0

        for emp in employees:
            basic = float(emp.base_salary)
            hra = round(0.40 * basic, 2)
            special = round(0.10 * basic, 2)
            medical = 1500.0 if basic > 0 else 0.0

            # Approved incentives for this month
            incentives = await self.repo.list_incentives(
                employee_id=emp.id, month=data.period_month, year=data.period_year
            )
            incentive_amt = sum(inc.calculated_amount for inc in incentives if inc.status == IncentiveStatus.APPROVED)

            gross = round(basic + hra + special + medical + incentive_amt, 2)

            # Deductions
            pf = round(min(basic * 0.12, 1800.0), 2)
            prof_tax = 200.0 if gross > 15000.0 else 0.0
            tds = round(max(0.0, (gross - 50000.0) * 0.10), 2) if gross > 50000.0 else 0.0
            insurance = 500.0 if basic > 0 else 0.0

            # Unpaid leave deduction
            daily_rate = basic / 30.0 if basic > 0 else 0.0
            emp_leaves = await self.repo.list_leave_requests(
                employee_id=emp.id, status=LeaveStatus.HR_APPROVED
            )
            unpaid_days = sum(
                l.days_count
                for l in emp_leaves
                if l.leave_type == LeaveType.UNPAID
                and l.start_date.month == data.period_month
                and l.start_date.year == data.period_year
            )
            unpaid_deduction = round(daily_rate * unpaid_days, 2)

            deductions = round(pf + prof_tax + tds + insurance + unpaid_deduction, 2)
            net_salary = round(max(0.0, gross - deductions), 2)

            await self.repo.create_payslip(
                {
                    "payroll_run_id": payroll_run.id,
                    "employee_id": emp.id,
                    "clinic_id": emp.clinic_id or (data.clinic_id or emp.id),
                    "period_month": data.period_month,
                    "period_year": data.period_year,
                    "basic_salary": basic,
                    "hra_allowance": hra,
                    "special_allowance": special,
                    "medical_allowance": medical,
                    "other_allowance": 0.0,
                    "incentive_amount": incentive_amt,
                    "overtime_amount": 0.0,
                    "bonus_amount": 0.0,
                    "gross_earnings": gross,
                    "pf_deduction": pf,
                    "professional_tax": prof_tax,
                    "tds_tax": tds,
                    "insurance_deduction": insurance,
                    "unpaid_leave_deduction": unpaid_deduction,
                    "other_deductions": 0.0,
                    "total_deductions": deductions,
                    "net_salary": net_salary,
                    "status": PayslipStatus.GENERATED,
                }
            )

            total_gross += gross
            total_deductions += deductions
            total_net += net_salary

        payroll_run.total_gross = round(total_gross, 2)
        payroll_run.total_deductions = round(total_deductions, 2)
        payroll_run.total_net = round(total_net, 2)
        payroll_run.total_employees = len(employees)
        await self.db.commit()
        await self.db.refresh(payroll_run)

        return payroll_run

    async def get_payroll_run(self, run_id: UUID) -> PayrollRun:
        run = await self.repo.get_payroll_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll run not found")
        return run

    async def list_payroll_runs(
        self, organization_id: UUID | None = None, clinic_id: UUID | None = None
    ) -> list[PayrollRun]:
        return await self.repo.list_payroll_runs(organization_id, clinic_id)

    async def list_payslips_for_run(self, run_id: UUID) -> list[Payslip]:
        return await self.repo.list_payslips_for_run(run_id)

    async def list_payslips_for_employee(self, employee_id: UUID) -> list[Payslip]:
        return await self.repo.list_payslips_for_employee(employee_id)

    # ---------------------------------------------------------
    # Performance Reviews
    # ---------------------------------------------------------
    async def create_performance_review(self, data: PerformanceReviewCreate) -> PerformanceReview:
        # Calculate weighted average overall rating
        rev_dict = data.model_dump()
        c = data.clinical_skills_rating
        p = data.patient_satisfaction_rating
        pt = data.punctuality_rating
        t = data.teamwork_rating
        pr = data.protocol_adherence_rating
        rev_dict["overall_rating"] = round(c * 0.30 + p * 0.25 + pr * 0.20 + t * 0.15 + pt * 0.10, 1)
        return await self.repo.create_performance_review(rev_dict)

    async def list_performance_reviews(
        self, clinic_id: UUID | None = None, employee_id: UUID | None = None
    ) -> list[PerformanceReview]:
        return await self.repo.list_performance_reviews(clinic_id, employee_id)

    # ---------------------------------------------------------
    # Training & Doctor Credentialing
    # ---------------------------------------------------------
    async def create_training_course(self, data: dict) -> TrainingCourse:
        return await self.repo.create_training_course(data)

    async def list_training_courses(self, organization_id: UUID | None = None) -> list[TrainingCourse]:
        return await self.repo.list_training_courses(organization_id)

    async def log_training_record(self, data: dict) -> EmployeeTrainingRecord:
        return await self.repo.create_employee_training_record(data)

    async def list_employee_training_records(self, employee_id: UUID) -> list[EmployeeTrainingRecord]:
        return await self.repo.list_employee_training_records(employee_id)

    # ---------------------------------------------------------
    # Recruitment
    # ---------------------------------------------------------
    async def create_job_opening(self, data: dict) -> JobOpening:
        return await self.repo.create_job_opening(data)

    async def list_job_openings(
        self, organization_id: UUID | None = None, clinic_id: UUID | None = None, status_filter: JobStatus | None = None
    ) -> list[JobOpening]:
        return await self.repo.list_job_openings(organization_id, clinic_id, status_filter)

    async def create_job_applicant(self, data: dict) -> JobApplicant:
        return await self.repo.create_job_applicant(data)

    async def list_job_applicants(
        self, job_opening_id: UUID | None = None, stage: ApplicantStage | None = None
    ) -> list[JobApplicant]:
        return await self.repo.list_job_applicants(job_opening_id, stage)

    async def create_interview_schedule(self, data: dict) -> InterviewSchedule:
        return await self.repo.create_interview_schedule(data)

    async def list_interview_schedules(self, applicant_id: UUID) -> list[InterviewSchedule]:
        return await self.repo.list_interview_schedules(applicant_id)

    # ---------------------------------------------------------
    # Employee Documents
    # ---------------------------------------------------------
    async def create_employee_document(self, data: dict) -> EmployeeDocument:
        return await self.repo.create_employee_document(data)

    async def list_employee_documents(self, employee_id: UUID) -> list[EmployeeDocument]:
        return await self.repo.list_employee_documents(employee_id)

    # ---------------------------------------------------------
    # Dashboard Aggregations
    # ---------------------------------------------------------
    async def get_dashboard_metrics(
        self, clinic_id: UUID | None = None, organization_id: UUID | None = None
    ) -> dict:
        return await self.repo.get_hr_dashboard_metrics(clinic_id, organization_id)
