from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hr import (
    ApplicantStage,
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    EmployeeDocument,
    EmployeeIncentive,
    EmployeeStatus,
    EmployeeTrainingRecord,
    InterviewSchedule,
    JobApplicant,
    JobOpening,
    JobStatus,
    LeaveAllocation,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    PayrollRun,
    Payslip,
    PerformanceReview,
    ScheduleStatus,
    StaffSchedule,
    TrainingCourse,
    WorkShift,
)


class HRRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # Employees
    # ---------------------------------------------------------
    async def create_employee(self, data: dict) -> Employee:
        employee = Employee(**data)
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get_employee_by_id(self, employee_id: UUID) -> Employee | None:
        stmt = select(Employee).where(Employee.id == employee_id, Employee.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_employee_by_code(self, employee_code: str, organization_id: UUID | None = None) -> Employee | None:
        stmt = select(Employee).where(
            Employee.employee_code == employee_code,
            Employee.deleted_at.is_(None)
        )
        if organization_id:
            stmt = stmt.where(Employee.organization_id == organization_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_employee_by_user_id(self, user_id: UUID) -> Employee | None:
        stmt = select(Employee).where(Employee.user_id == user_id, Employee.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_employees(
        self,
        organization_id: UUID | None = None,
        clinic_id: UUID | None = None,
        department_id: UUID | None = None,
        status: EmployeeStatus | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Employee]:
        stmt = select(Employee).where(Employee.deleted_at.is_(None))
        if organization_id:
            stmt = stmt.where(Employee.organization_id == organization_id)
        if clinic_id:
            stmt = stmt.where(Employee.clinic_id == clinic_id)
        if department_id:
            stmt = stmt.where(Employee.department_id == department_id)
        if status:
            stmt = stmt.where(Employee.status == status)
        if search:
            q = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Employee.first_name.ilike(q),
                    Employee.last_name.ilike(q),
                    Employee.employee_code.ilike(q),
                    Employee.email.ilike(q),
                    Employee.designation.ilike(q),
                )
            )
        stmt = stmt.order_by(Employee.first_name.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_employee(self, employee_id: UUID, updates: dict) -> Employee | None:
        employee = await self.get_employee_by_id(employee_id)
        if not employee:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(employee, key):
                setattr(employee, key, value)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    # ---------------------------------------------------------
    # Work Shifts
    # ---------------------------------------------------------
    async def create_work_shift(self, data: dict) -> WorkShift:
        shift = WorkShift(**data)
        self.db.add(shift)
        await self.db.commit()
        await self.db.refresh(shift)
        return shift

    async def get_work_shift_by_id(self, shift_id: UUID) -> WorkShift | None:
        stmt = select(WorkShift).where(WorkShift.id == shift_id, WorkShift.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_work_shifts(
        self,
        organization_id: UUID | None = None,
        clinic_id: UUID | None = None,
    ) -> list[WorkShift]:
        stmt = select(WorkShift).where(WorkShift.deleted_at.is_(None), WorkShift.is_active.is_(True))
        if organization_id:
            stmt = stmt.where(or_(WorkShift.organization_id == organization_id, WorkShift.organization_id.is_(None)))
        if clinic_id:
            stmt = stmt.where(or_(WorkShift.clinic_id == clinic_id, WorkShift.clinic_id.is_(None)))
        stmt = stmt.order_by(WorkShift.start_time.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Staff Schedules & Conflict Detection
    # ---------------------------------------------------------
    async def check_schedule_conflict(
        self,
        clinic_id: UUID,
        employee_id: UUID,
        schedule_date: date,
        start_time: time,
        end_time: time,
        chair_id: UUID | None = None,
        exclude_schedule_id: UUID | None = None,
    ) -> tuple[bool, str | None, str]:
        # 1. Check if employee is already scheduled during this overlapping time
        emp_stmt = select(StaffSchedule).where(
            StaffSchedule.employee_id == employee_id,
            StaffSchedule.schedule_date == schedule_date,
            StaffSchedule.status != ScheduleStatus.CANCELLED,
            StaffSchedule.deleted_at.is_(None),
            and_(
                StaffSchedule.start_time < end_time,
                StaffSchedule.end_time > start_time,
            ),
        )
        if exclude_schedule_id:
            emp_stmt = emp_stmt.where(StaffSchedule.id != exclude_schedule_id)
        emp_res = await self.db.execute(emp_stmt)
        if emp_res.scalar_one_or_none():
            return True, "EMPLOYEE_DOUBLE_BOOKED", "Employee already has an overlapping shift on this date."

        # 2. Check if chair is already booked during this overlapping time
        if chair_id:
            chair_stmt = select(StaffSchedule).where(
                StaffSchedule.chair_id == chair_id,
                StaffSchedule.schedule_date == schedule_date,
                StaffSchedule.status != ScheduleStatus.CANCELLED,
                StaffSchedule.deleted_at.is_(None),
                and_(
                    StaffSchedule.start_time < end_time,
                    StaffSchedule.end_time > start_time,
                ),
            )
            if exclude_schedule_id:
                chair_stmt = chair_stmt.where(StaffSchedule.id != exclude_schedule_id)
            chair_res = await self.db.execute(chair_stmt)
            if chair_res.scalar_one_or_none():
                return True, "CHAIR_DOUBLE_BOOKED", "Operatory chair is already assigned to another staff member during this slot."

        return False, None, "No scheduling conflicts detected."

    async def create_staff_schedule(self, data: dict) -> StaffSchedule:
        schedule = StaffSchedule(**data)
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    async def list_staff_schedules(
        self,
        clinic_id: UUID,
        start_date: date,
        end_date: date,
        employee_id: UUID | None = None,
    ) -> list[StaffSchedule]:
        stmt = select(StaffSchedule).where(
            StaffSchedule.clinic_id == clinic_id,
            StaffSchedule.schedule_date >= start_date,
            StaffSchedule.schedule_date <= end_date,
            StaffSchedule.deleted_at.is_(None),
        )
        if employee_id:
            stmt = stmt.where(StaffSchedule.employee_id == employee_id)
        stmt = stmt.order_by(StaffSchedule.schedule_date.asc(), StaffSchedule.start_time.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Attendance Records
    # ---------------------------------------------------------
    async def get_attendance_record(self, employee_id: UUID, record_date: date) -> AttendanceRecord | None:
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == record_date,
            AttendanceRecord.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_attendance_record(self, data: dict) -> AttendanceRecord:
        record = AttendanceRecord(**data)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_attendance_record(self, record_id: UUID, updates: dict) -> AttendanceRecord | None:
        stmt = select(AttendanceRecord).where(AttendanceRecord.id == record_id, AttendanceRecord.deleted_at.is_(None))
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(record, key):
                setattr(record, key, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_attendance(
        self,
        clinic_id: UUID,
        record_date: date,
        employee_id: UUID | None = None,
    ) -> list[AttendanceRecord]:
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.clinic_id == clinic_id,
            AttendanceRecord.date == record_date,
            AttendanceRecord.deleted_at.is_(None),
        )
        if employee_id:
            stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Leave Management
    # ---------------------------------------------------------
    async def get_or_create_leave_allocation(
        self, employee_id: UUID, year: int, leave_type: LeaveType, default_days: float = 12.0
    ) -> LeaveAllocation:
        stmt = select(LeaveAllocation).where(
            LeaveAllocation.employee_id == employee_id,
            LeaveAllocation.year == year,
            LeaveAllocation.leave_type == leave_type,
            LeaveAllocation.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        allocation = result.scalar_one_or_none()
        if not allocation:
            allocation = LeaveAllocation(
                employee_id=employee_id,
                year=year,
                leave_type=leave_type,
                total_days=default_days,
                used_days=0.0,
                pending_days=0.0,
            )
            self.db.add(allocation)
            await self.db.commit()
            await self.db.refresh(allocation)
        return allocation

    async def list_leave_allocations(self, employee_id: UUID, year: int) -> list[LeaveAllocation]:
        stmt = select(LeaveAllocation).where(
            LeaveAllocation.employee_id == employee_id,
            LeaveAllocation.year == year,
            LeaveAllocation.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_leave_request(self, data: dict) -> LeaveRequest:
        leave_request = LeaveRequest(**data)
        self.db.add(leave_request)
        await self.db.commit()
        await self.db.refresh(leave_request)
        return leave_request

    async def get_leave_request_by_id(self, request_id: UUID) -> LeaveRequest | None:
        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id, LeaveRequest.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_leave_requests(
        self,
        clinic_id: UUID | None = None,
        employee_id: UUID | None = None,
        status: LeaveStatus | None = None,
    ) -> list[LeaveRequest]:
        stmt = select(LeaveRequest).where(LeaveRequest.deleted_at.is_(None))
        if clinic_id:
            stmt = stmt.where(LeaveRequest.clinic_id == clinic_id)
        if employee_id:
            stmt = stmt.where(LeaveRequest.employee_id == employee_id)
        if status:
            stmt = stmt.where(LeaveRequest.status == status)
        stmt = stmt.order_by(LeaveRequest.start_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_leave_request(self, request_id: UUID, updates: dict) -> LeaveRequest | None:
        leave_req = await self.get_leave_request_by_id(request_id)
        if not leave_req:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(leave_req, key):
                setattr(leave_req, key, value)
        await self.db.commit()
        await self.db.refresh(leave_req)
        return leave_req

    # ---------------------------------------------------------
    # Payroll Runs & Payslips
    # ---------------------------------------------------------
    async def create_payroll_run(self, data: dict) -> PayrollRun:
        run = PayrollRun(**data)
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_payroll_run_by_id(self, run_id: UUID) -> PayrollRun | None:
        stmt = select(PayrollRun).where(PayrollRun.id == run_id, PayrollRun.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_payroll_runs(
        self, organization_id: UUID | None = None, clinic_id: UUID | None = None
    ) -> list[PayrollRun]:
        stmt = select(PayrollRun).where(PayrollRun.deleted_at.is_(None))
        if organization_id:
            stmt = stmt.where(PayrollRun.organization_id == organization_id)
        if clinic_id:
            stmt = stmt.where(PayrollRun.clinic_id == clinic_id)
        stmt = stmt.order_by(PayrollRun.period_year.desc(), PayrollRun.period_month.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_payslip(self, data: dict) -> Payslip:
        payslip = Payslip(**data)
        self.db.add(payslip)
        await self.db.commit()
        await self.db.refresh(payslip)
        return payslip

    async def list_payslips_for_run(self, run_id: UUID) -> list[Payslip]:
        stmt = select(Payslip).where(Payslip.payroll_run_id == run_id, Payslip.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_payslips_for_employee(self, employee_id: UUID) -> list[Payslip]:
        stmt = select(Payslip).where(Payslip.employee_id == employee_id, Payslip.deleted_at.is_(None))
        stmt = stmt.order_by(Payslip.period_year.desc(), Payslip.period_month.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Incentives
    # ---------------------------------------------------------
    async def create_incentive(self, data: dict) -> EmployeeIncentive:
        incentive = EmployeeIncentive(**data)
        self.db.add(incentive)
        await self.db.commit()
        await self.db.refresh(incentive)
        return incentive

    async def list_incentives(
        self, employee_id: UUID | None = None, month: int | None = None, year: int | None = None
    ) -> list[EmployeeIncentive]:
        stmt = select(EmployeeIncentive).where(EmployeeIncentive.deleted_at.is_(None))
        if employee_id:
            stmt = stmt.where(EmployeeIncentive.employee_id == employee_id)
        if month:
            stmt = stmt.where(EmployeeIncentive.period_month == month)
        if year:
            stmt = stmt.where(EmployeeIncentive.period_year == year)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Performance Reviews
    # ---------------------------------------------------------
    async def create_performance_review(self, data: dict) -> PerformanceReview:
        review = PerformanceReview(**data)
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def list_performance_reviews(
        self, clinic_id: UUID | None = None, employee_id: UUID | None = None
    ) -> list[PerformanceReview]:
        stmt = select(PerformanceReview).where(PerformanceReview.deleted_at.is_(None))
        if clinic_id:
            stmt = stmt.where(PerformanceReview.clinic_id == clinic_id)
        if employee_id:
            stmt = stmt.where(PerformanceReview.employee_id == employee_id)
        stmt = stmt.order_by(PerformanceReview.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Training Courses & Records
    # ---------------------------------------------------------
    async def create_training_course(self, data: dict) -> TrainingCourse:
        course = TrainingCourse(**data)
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def list_training_courses(self, organization_id: UUID | None = None) -> list[TrainingCourse]:
        stmt = select(TrainingCourse).where(TrainingCourse.deleted_at.is_(None))
        if organization_id:
            stmt = stmt.where(or_(TrainingCourse.organization_id == organization_id, TrainingCourse.organization_id.is_(None)))
        stmt = stmt.order_by(TrainingCourse.title.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_employee_training_record(self, data: dict) -> EmployeeTrainingRecord:
        record = EmployeeTrainingRecord(**data)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_employee_training_records(self, employee_id: UUID) -> list[EmployeeTrainingRecord]:
        stmt = select(EmployeeTrainingRecord).where(
            EmployeeTrainingRecord.employee_id == employee_id,
            EmployeeTrainingRecord.deleted_at.is_(None)
        )
        stmt = stmt.order_by(EmployeeTrainingRecord.completion_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Recruitment
    # ---------------------------------------------------------
    async def create_job_opening(self, data: dict) -> JobOpening:
        job = JobOpening(**data)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def list_job_openings(
        self, organization_id: UUID | None = None, clinic_id: UUID | None = None, status: JobStatus | None = None
    ) -> list[JobOpening]:
        stmt = select(JobOpening).where(JobOpening.deleted_at.is_(None))
        if organization_id:
            stmt = stmt.where(JobOpening.organization_id == organization_id)
        if clinic_id:
            stmt = stmt.where(JobOpening.clinic_id == clinic_id)
        if status:
            stmt = stmt.where(JobOpening.status == status)
        stmt = stmt.order_by(JobOpening.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_job_applicant(self, data: dict) -> JobApplicant:
        applicant = JobApplicant(**data)
        self.db.add(applicant)
        await self.db.commit()
        await self.db.refresh(applicant)
        return applicant

    async def list_job_applicants(
        self, job_opening_id: UUID | None = None, stage: ApplicantStage | None = None
    ) -> list[JobApplicant]:
        stmt = select(JobApplicant).where(JobApplicant.deleted_at.is_(None))
        if job_opening_id:
            stmt = stmt.where(JobApplicant.job_opening_id == job_opening_id)
        if stage:
            stmt = stmt.where(JobApplicant.current_stage == stage)
        stmt = stmt.order_by(JobApplicant.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_interview_schedule(self, data: dict) -> InterviewSchedule:
        interview = InterviewSchedule(**data)
        self.db.add(interview)
        await self.db.commit()
        await self.db.refresh(interview)
        return interview

    async def list_interview_schedules(self, applicant_id: UUID) -> list[InterviewSchedule]:
        stmt = select(InterviewSchedule).where(
            InterviewSchedule.applicant_id == applicant_id,
            InterviewSchedule.deleted_at.is_(None)
        )
        stmt = stmt.order_by(InterviewSchedule.scheduled_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Employee Documents
    # ---------------------------------------------------------
    async def create_employee_document(self, data: dict) -> EmployeeDocument:
        doc = EmployeeDocument(**data)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_employee_documents(self, employee_id: UUID) -> list[EmployeeDocument]:
        stmt = select(EmployeeDocument).where(
            EmployeeDocument.employee_id == employee_id,
            EmployeeDocument.deleted_at.is_(None)
        )
        stmt = stmt.order_by(EmployeeDocument.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------
    # Dashboard Aggregations
    # ---------------------------------------------------------
    async def get_hr_dashboard_metrics(
        self, clinic_id: UUID | None = None, organization_id: UUID | None = None
    ) -> dict:
        today = datetime.now(UTC).date()

        # Headcount query
        emp_stmt = select(
            func.count(Employee.id).label("total"),
            func.count(Employee.id).filter(Employee.status == EmployeeStatus.ACTIVE).label("active"),
            func.count(Employee.id).filter(Employee.status == EmployeeStatus.ON_LEAVE).label("on_leave"),
        ).where(Employee.deleted_at.is_(None))
        if clinic_id:
            emp_stmt = emp_stmt.where(Employee.clinic_id == clinic_id)
        if organization_id:
            emp_stmt = emp_stmt.where(Employee.organization_id == organization_id)
        emp_res = (await self.db.execute(emp_stmt)).one()

        # Today's attendance
        att_stmt = select(
            func.count(AttendanceRecord.id).label("total"),
            func.count(AttendanceRecord.id).filter(AttendanceRecord.status == AttendanceStatus.PRESENT).label("present"),
            func.count(AttendanceRecord.id).filter(AttendanceRecord.is_late.is_(True)).label("late"),
        ).where(AttendanceRecord.date == today, AttendanceRecord.deleted_at.is_(None))
        if clinic_id:
            att_stmt = att_stmt.where(AttendanceRecord.clinic_id == clinic_id)
        att_res = (await self.db.execute(att_stmt)).one()

        # Scheduled today
        sched_stmt = select(func.count(StaffSchedule.id)).where(
            StaffSchedule.schedule_date == today,
            StaffSchedule.status != ScheduleStatus.CANCELLED,
            StaffSchedule.deleted_at.is_(None),
        )
        if clinic_id:
            sched_stmt = sched_stmt.where(StaffSchedule.clinic_id == clinic_id)
        scheduled_count = (await self.db.execute(sched_stmt)).scalar() or 0

        # Pending leaves
        leave_stmt = select(func.count(LeaveRequest.id)).where(
            LeaveRequest.status.in_([LeaveStatus.SUBMITTED, LeaveStatus.MANAGER_APPROVED]),
            LeaveRequest.deleted_at.is_(None),
        )
        if clinic_id:
            leave_stmt = leave_stmt.where(LeaveRequest.clinic_id == clinic_id)
        pending_leaves = (await self.db.execute(leave_stmt)).scalar() or 0

        # Open job positions
        job_stmt = select(func.sum(JobOpening.open_positions)).where(
            JobOpening.status == JobStatus.OPEN,
            JobOpening.deleted_at.is_(None),
        )
        if clinic_id:
            job_stmt = job_stmt.where(JobOpening.clinic_id == clinic_id)
        open_jobs = (await self.db.execute(job_stmt)).scalar() or 0

        # Licenses expiring in next 60 days
        expiry_cutoff = date.fromordinal(today.toordinal() + 60)
        lic_stmt = select(func.count(Employee.id)).where(
            Employee.license_expiry_date.isnot(None),
            Employee.license_expiry_date >= today,
            Employee.license_expiry_date <= expiry_cutoff,
            Employee.deleted_at.is_(None),
        )
        if clinic_id:
            lic_stmt = lic_stmt.where(Employee.clinic_id == clinic_id)
        lic_expiring = (await self.db.execute(lic_stmt)).scalar() or 0

        # Current month estimated payroll sum
        sal_stmt = select(func.sum(Employee.base_salary)).where(
            Employee.status == EmployeeStatus.ACTIVE,
            Employee.deleted_at.is_(None),
        )
        if clinic_id:
            sal_stmt = sal_stmt.where(Employee.clinic_id == clinic_id)
        raw_payroll = (await self.db.execute(sal_stmt)).scalar() or 0.0
        monthly_payroll_estimate = getattr(raw_payroll, "base_salary", raw_payroll) or 0.0

        total_headcount = emp_res.total or 0
        active_employees = emp_res.active or 0
        on_leave = emp_res.on_leave or 0
        present = att_res.present or 0
        late = att_res.late or 0
        att_rate = round((present / scheduled_count * 100) if scheduled_count > 0 else 100.0, 1)

        raw_open_jobs = getattr(open_jobs, "open_positions", open_jobs) or 0

        return {
            "total_headcount": total_headcount,
            "active_employees": active_employees,
            "on_leave_employees": on_leave,
            "today_scheduled": scheduled_count,
            "today_present": present,
            "today_late": late,
            "attendance_rate": att_rate,
            "pending_leaves": pending_leaves,
            "current_month_payroll_total": float(monthly_payroll_estimate),
            "open_job_positions": int(raw_open_jobs),
            "licenses_expiring_soon": int(getattr(lic_expiring, "id", lic_expiring) if not isinstance(lic_expiring, int) else lic_expiring),
        }
