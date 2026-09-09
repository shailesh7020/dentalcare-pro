from __future__ import annotations

from datetime import date, datetime, time
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin


class EmploymentType(StrEnum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    CONSULTANT = "CONSULTANT"
    INTERN = "INTERN"


class EmployeeStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    RESIGNED = "RESIGNED"
    RETIRED = "RETIRED"


class ShiftType(StrEnum):
    REGULAR = "REGULAR"
    ROTATING = "ROTATING"
    SPLIT = "SPLIT"
    EMERGENCY = "EMERGENCY"


class ScheduleStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    ABSENT = "ABSENT"
    CANCELLED = "CANCELLED"


class AttendanceMethod(StrEnum):
    MANUAL = "MANUAL"
    QR_CODE = "QR_CODE"
    RFID = "RFID"
    BIOMETRIC = "BIOMETRIC"


class AttendanceStatus(StrEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"
    ON_LEAVE = "ON_LEAVE"


class LeaveType(StrEnum):
    CASUAL = "CASUAL"
    SICK = "SICK"
    ANNUAL = "ANNUAL"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    EMERGENCY = "EMERGENCY"
    UNPAID = "UNPAID"


class LeaveStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    MANAGER_APPROVED = "MANAGER_APPROVED"
    HR_APPROVED = "HR_APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PayrollStatus(StrEnum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PayslipStatus(StrEnum):
    GENERATED = "GENERATED"
    APPROVED = "APPROVED"
    PAID = "PAID"


class IncentiveCriterion(StrEnum):
    TREATMENTS_COMPLETED = "TREATMENTS_COMPLETED"
    REVENUE_GENERATED = "REVENUE_GENERATED"
    PATIENT_SATISFACTION = "PATIENT_SATISFACTION"
    COLLECTION_TARGETS = "COLLECTION_TARGETS"
    ATTENDANCE_PERFECT = "ATTENDANCE_PERFECT"
    CUSTOM = "CUSTOM"


class IncentiveStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    INCLUDED_IN_PAYROLL = "INCLUDED_IN_PAYROLL"


class ReviewCycle(StrEnum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ReviewStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    COMPLETED = "COMPLETED"


class CourseType(StrEnum):
    CONTINUING_EDUCATION = "CONTINUING_EDUCATION"
    INFECTION_CONTROL = "INFECTION_CONTROL"
    CPR_BLS = "CPR_BLS"
    RADIATION_SAFETY = "RADIATION_SAFETY"
    CLINICAL_SPECIALTY = "CLINICAL_SPECIALTY"
    COMPLIANCE = "COMPLIANCE"


class TrainingRecordStatus(StrEnum):
    ENROLLED = "ENROLLED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class JobStatus(StrEnum):
    OPEN = "OPEN"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"


class ApplicantStage(StrEnum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    OFFERED = "OFFERED"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


class InterviewType(StrEnum):
    TECHNICAL = "TECHNICAL"
    CLINICAL_DEMO = "CLINICAL_DEMO"
    HR = "HR"
    FINAL = "FINAL"


class InterviewResult(StrEnum):
    PENDING = "PENDING"
    RECOMMENDED = "RECOMMENDED"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"


class DocumentType(StrEnum):
    CONTRACT = "CONTRACT"
    CERTIFICATE = "CERTIFICATE"
    DENTAL_LICENSE = "DENTAL_LICENSE"
    ID_PROOF = "ID_PROOF"
    TAX_DOCUMENT = "TAX_DOCUMENT"
    EDUCATIONAL = "EDUCATIONAL"
    PERFORMANCE_REPORT = "PERFORMANCE_REPORT"


class Employee(Base, UUIDAuditMixin):
    __tablename__ = "employees"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True, nullable=True
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), index=True, nullable=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, index=True, nullable=True
    )
    employee_code: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gender: Mapped[str] = mapped_column(String(20), default="OTHER", nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    emergency_contact_relation: Mapped[str | None] = mapped_column(String(60), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(120), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(120), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    license_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="emp_employment_type"),
        default=EmploymentType.FULL_TIME,
        nullable=False,
    )
    reporting_manager_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus, name="emp_status"),
        default=EmployeeStatus.ACTIVE,
        nullable=False,
    )
    base_salary: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    bank_ifsc_or_routing: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tax_id_number: Mapped[str | None] = mapped_column(String(60), nullable=True)

    schedules: Mapped[list[StaffSchedule]] = relationship("StaffSchedule", back_populates="employee", cascade="all, delete-orphan")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    leave_requests: Mapped[list[LeaveRequest]] = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")
    leave_allocations: Mapped[list[LeaveAllocation]] = relationship("LeaveAllocation", back_populates="employee", cascade="all, delete-orphan")
    payslips: Mapped[list[Payslip]] = relationship("Payslip", back_populates="employee", cascade="all, delete-orphan")
    training_records: Mapped[list[EmployeeTrainingRecord]] = relationship("EmployeeTrainingRecord", back_populates="employee", cascade="all, delete-orphan")
    documents: Mapped[list[EmployeeDocument]] = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")


class WorkShift(Base, UUIDAuditMixin):
    __tablename__ = "work_shifts"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    shift_type: Mapped[ShiftType] = mapped_column(
        Enum(ShiftType, name="ws_shift_type"), default=ShiftType.REGULAR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StaffSchedule(Base, UUIDAuditMixin):
    __tablename__ = "staff_schedules"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    shift_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("work_shifts.id", ondelete="SET NULL"), nullable=True
    )
    chair_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chairs.id", ondelete="SET NULL"), nullable=True
    )
    schedule_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_split_shift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    split_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    split_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, name="ss_status"), default=ScheduleStatus.SCHEDULED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped[Employee] = relationship("Employee", back_populates="schedules")


class AttendanceRecord(Base, UUIDAuditMixin):
    __tablename__ = "attendance_records"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_method: Mapped[AttendanceMethod] = mapped_column(
        Enum(AttendanceMethod, name="att_method"), default=AttendanceMethod.MANUAL, nullable=False
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="att_status"), default=AttendanceStatus.PRESENT, nullable=False
    )
    break_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_early_departure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    early_departure_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped[Employee] = relationship("Employee", back_populates="attendance_records")


class LeaveAllocation(Base, UUIDAuditMixin):
    __tablename__ = "leave_allocations"

    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, name="la_leave_type"), nullable=False
    )
    total_days: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    used_days: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pending_days: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="leave_allocations")


class LeaveRequest(Base, UUIDAuditMixin):
    __tablename__ = "leave_requests"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, name="lr_leave_type"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, name="lr_status"), default=LeaveStatus.DRAFT, nullable=False
    )
    manager_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    manager_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hr_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    hr_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    hr_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = relationship("Employee", back_populates="leave_requests")


class PayrollRun(Base, UUIDAuditMixin):
    __tablename__ = "payroll_runs"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True
    )
    run_number: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus, name="pr_status"), default=PayrollStatus.DRAFT, nullable=False
    )
    total_gross: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_net: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_employees: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    payslips: Mapped[list[Payslip]] = relationship("Payslip", back_populates="payroll_run", cascade="all, delete-orphan")


class Payslip(Base, UUIDAuditMixin):
    __tablename__ = "payslips"

    payroll_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    basic_salary: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hra_allowance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    special_allowance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    medical_allowance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    other_allowance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    incentive_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overtime_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bonus_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gross_earnings: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pf_deduction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    professional_tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tds_tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    insurance_deduction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unpaid_leave_deduction: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    other_deductions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_salary: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[PayslipStatus] = mapped_column(
        Enum(PayslipStatus, name="ps_status"), default=PayslipStatus.GENERATED, nullable=False
    )
    payment_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = relationship("Employee", back_populates="payslips")
    payroll_run: Mapped[PayrollRun] = relationship("PayrollRun", back_populates="payslips")


class EmployeeIncentive(Base, UUIDAuditMixin):
    __tablename__ = "employee_incentives"

    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    criterion_type: Mapped[IncentiveCriterion] = mapped_column(
        Enum(IncentiveCriterion, name="ei_criterion"), nullable=False
    )
    target_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    achieved_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rate_or_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    calculated_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[IncentiveStatus] = mapped_column(
        Enum(IncentiveStatus, name="ei_status"), default=IncentiveStatus.PENDING, nullable=False
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PerformanceReview(Base, UUIDAuditMixin):
    __tablename__ = "performance_reviews"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_cycle: Mapped[ReviewCycle] = mapped_column(
        Enum(ReviewCycle, name="pr_cycle"), default=ReviewCycle.QUARTERLY, nullable=False
    )
    review_period: Mapped[str] = mapped_column(String(40), nullable=False)
    clinical_skills_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    patient_satisfaction_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    punctuality_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    teamwork_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    protocol_adherence_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    overall_rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    kpi_details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    areas_of_improvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals_next_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_needs: Mapped[str | None] = mapped_column(Text, nullable=True)
    employee_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="pr_rev_status"), default=ReviewStatus.DRAFT, nullable=False
    )


class TrainingCourse(Base, UUIDAuditMixin):
    __tablename__ = "training_courses"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(160), nullable=False)
    course_type: Mapped[CourseType] = mapped_column(
        Enum(CourseType, name="tc_course_type"), default=CourseType.CONTINUING_EDUCATION, nullable=False
    )
    credits_hours: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validity_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmployeeTrainingRecord(Base, UUIDAuditMixin):
    __tablename__ = "employee_training_records"

    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    course_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("training_courses.id", ondelete="SET NULL"), nullable=True
    )
    course_title: Mapped[str] = mapped_column(String(200), nullable=False)
    completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    certificate_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[TrainingRecordStatus] = mapped_column(
        Enum(TrainingRecordStatus, name="etr_status"), default=TrainingRecordStatus.COMPLETED, nullable=False
    )

    employee: Mapped[Employee] = relationship("Employee", back_populates="training_records")


class JobOpening(Base, UUIDAuditMixin):
    __tablename__ = "job_openings"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="jo_employment_type"), default=EmploymentType.FULL_TIME, nullable=False
    )
    open_positions: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    experience_years_min: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jo_status"), default=JobStatus.OPEN, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    applicants: Mapped[list[JobApplicant]] = relationship("JobApplicant", back_populates="job_opening", cascade="all, delete-orphan")


class JobApplicant(Base, UUIDAuditMixin):
    __tablename__ = "job_applicants"

    job_opening_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_openings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    resume_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experience_years: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_stage: Mapped[ApplicantStage] = mapped_column(
        Enum(ApplicantStage, name="ja_stage"), default=ApplicantStage.APPLIED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    job_opening: Mapped[JobOpening] = relationship("JobOpening", back_populates="applicants")
    interviews: Mapped[list[InterviewSchedule]] = relationship("InterviewSchedule", back_populates="applicant", cascade="all, delete-orphan")


class InterviewSchedule(Base, UUIDAuditMixin):
    __tablename__ = "interview_schedules"

    applicant_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_applicants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    interviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, name="is_type"), default=InterviewType.TECHNICAL, nullable=False
    )
    feedback_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[InterviewResult] = mapped_column(
        Enum(InterviewResult, name="is_result"), default=InterviewResult.PENDING, nullable=False
    )

    applicant: Mapped[JobApplicant] = relationship("JobApplicant", back_populates="interviews")


class EmployeeDocument(Base, UUIDAuditMixin):
    __tablename__ = "employee_documents"

    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="ed_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    file_url: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), default="application/pdf", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="documents")
