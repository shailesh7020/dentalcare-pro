from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.hr import (
    ApplicantStage,
    AttendanceMethod,
    AttendanceStatus,
    CourseType,
    DocumentType,
    EmployeeStatus,
    EmploymentType,
    IncentiveCriterion,
    IncentiveStatus,
    InterviewResult,
    InterviewType,
    JobStatus,
    LeaveStatus,
    LeaveType,
    PayrollStatus,
    PayslipStatus,
    ReviewCycle,
    ReviewStatus,
    ScheduleStatus,
    ShiftType,
    TrainingRecordStatus,
)


# ---------------------------------------------------------
# Employee Schemas
# ---------------------------------------------------------
class EmployeeBase(BaseModel):
    employee_code: str = Field(..., max_length=40)
    first_name: str = Field(..., max_length=80)
    last_name: str = Field(..., max_length=80)
    email: EmailStr
    phone: str | None = None
    gender: str = "OTHER"
    date_of_birth: date | None = None
    profile_photo_url: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    address: str | None = None
    qualification: str | None = None
    specialization: str | None = None
    license_number: str | None = None
    license_expiry_date: date | None = None
    department_id: UUID | None = None
    designation: str = Field(..., max_length=100)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    reporting_manager_id: UUID | None = None
    joining_date: date
    exit_date: date | None = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    base_salary: float = 0.0
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_ifsc_or_routing: str | None = None
    tax_id_number: str | None = None


class EmployeeCreate(EmployeeBase):
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    user_id: UUID | None = None


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    profile_photo_url: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    address: str | None = None
    qualification: str | None = None
    specialization: str | None = None
    license_number: str | None = None
    license_expiry_date: date | None = None
    department_id: UUID | None = None
    designation: str | None = None
    employment_type: EmploymentType | None = None
    reporting_manager_id: UUID | None = None
    exit_date: date | None = None
    status: EmployeeStatus | None = None
    base_salary: float | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_ifsc_or_routing: str | None = None
    tax_id_number: str | None = None
    clinic_id: UUID | None = None
    user_id: UUID | None = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Work Shift Schemas
# ---------------------------------------------------------
class WorkShiftBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=30)
    start_time: time
    end_time: time
    break_minutes: int = 60
    shift_type: ShiftType = ShiftType.REGULAR
    is_active: bool = True


class WorkShiftCreate(WorkShiftBase):
    organization_id: UUID | None = None
    clinic_id: UUID | None = None


class WorkShiftUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = None
    shift_type: ShiftType | None = None
    is_active: bool | None = None


class WorkShiftResponse(WorkShiftBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Staff Schedule Schemas
# ---------------------------------------------------------
class StaffScheduleBase(BaseModel):
    employee_id: UUID
    shift_id: UUID | None = None
    chair_id: UUID | None = None
    schedule_date: date
    start_time: time
    end_time: time
    is_split_shift: bool = False
    split_start_time: time | None = None
    split_end_time: time | None = None
    status: ScheduleStatus = ScheduleStatus.SCHEDULED
    notes: str | None = None


class StaffScheduleCreate(StaffScheduleBase):
    organization_id: UUID | None = None
    clinic_id: UUID


class StaffScheduleUpdate(BaseModel):
    shift_id: UUID | None = None
    chair_id: UUID | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_split_shift: bool | None = None
    split_start_time: time | None = None
    split_end_time: time | None = None
    status: ScheduleStatus | None = None
    notes: str | None = None


class StaffScheduleResponse(StaffScheduleBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleConflictCheckRequest(BaseModel):
    clinic_id: UUID
    employee_id: UUID
    schedule_date: date
    start_time: time
    end_time: time
    chair_id: UUID | None = None
    exclude_schedule_id: UUID | None = None


class ScheduleConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflict_type: str | None = None  # "EMPLOYEE_DOUBLE_BOOKED", "CHAIR_DOUBLE_BOOKED", "SPLIT_REST_VIOLATION"
    message: str


# ---------------------------------------------------------
# Attendance Schemas
# ---------------------------------------------------------
class AttendanceRecordBase(BaseModel):
    employee_id: UUID
    date: date
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    entry_method: AttendanceMethod = AttendanceMethod.MANUAL
    status: AttendanceStatus = AttendanceStatus.PRESENT
    break_minutes: int = 0
    overtime_minutes: int = 0
    is_late: bool = False
    late_minutes: int = 0
    is_early_departure: bool = False
    early_departure_minutes: int = 0
    notes: str | None = None


class AttendanceRecordCreate(AttendanceRecordBase):
    organization_id: UUID | None = None
    clinic_id: UUID


class AttendanceRecordUpdate(BaseModel):
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    status: AttendanceStatus | None = None
    break_minutes: int | None = None
    overtime_minutes: int | None = None
    is_late: bool | None = None
    late_minutes: int | None = None
    is_early_departure: bool | None = None
    early_departure_minutes: int | None = None
    notes: str | None = None


class AttendanceRecordResponse(AttendanceRecordBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClockInRequest(BaseModel):
    clinic_id: UUID
    employee_id: UUID
    entry_method: AttendanceMethod = AttendanceMethod.MANUAL
    notes: str | None = None


class ClockOutRequest(BaseModel):
    notes: str | None = None


class AttendanceSummaryResponse(BaseModel):
    total_scheduled: int
    present_count: int
    late_count: int
    absent_count: int
    on_leave_count: int
    attendance_rate_percentage: float
    total_overtime_hours: float


# ---------------------------------------------------------
# Leave Schemas
# ---------------------------------------------------------
class LeaveAllocationBase(BaseModel):
    employee_id: UUID
    year: int
    leave_type: LeaveType
    total_days: float
    used_days: float = 0.0
    pending_days: float = 0.0


class LeaveAllocationCreate(LeaveAllocationBase):
    pass


class LeaveAllocationResponse(LeaveAllocationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_count: float = 1.0
    reason: str


class LeaveRequestCreate(LeaveRequestBase):
    organization_id: UUID | None = None
    clinic_id: UUID


class LeaveRequestUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    days_count: float | None = None
    reason: str | None = None
    status: LeaveStatus | None = None


class LeaveActionRequest(BaseModel):
    action: str  # "SUBMIT", "MANAGER_APPROVE", "MANAGER_REJECT", "HR_APPROVE", "HR_REJECT", "CANCEL"
    notes: str | None = None


class LeaveRequestResponse(LeaveRequestBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID
    status: LeaveStatus
    manager_id: UUID | None = None
    manager_notes: str | None = None
    manager_reviewed_at: datetime | None = None
    hr_id: UUID | None = None
    hr_notes: str | None = None
    hr_reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Payroll Schemas
# ---------------------------------------------------------
class PayrollRunBase(BaseModel):
    run_number: str
    period_month: int
    period_year: int
    status: PayrollStatus = PayrollStatus.DRAFT
    total_gross: float = 0.0
    total_deductions: float = 0.0
    total_net: float = 0.0
    total_employees: int = 0
    notes: str | None = None


class PayrollRunCreate(BaseModel):
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    period_month: int
    period_year: int
    notes: str | None = None


class PayrollRunResponse(PayrollRunBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayslipBase(BaseModel):
    payroll_run_id: UUID
    employee_id: UUID
    clinic_id: UUID
    period_month: int
    period_year: int
    basic_salary: float = 0.0
    hra_allowance: float = 0.0
    special_allowance: float = 0.0
    medical_allowance: float = 0.0
    other_allowance: float = 0.0
    incentive_amount: float = 0.0
    overtime_amount: float = 0.0
    bonus_amount: float = 0.0
    gross_earnings: float = 0.0
    pf_deduction: float = 0.0
    professional_tax: float = 0.0
    tds_tax: float = 0.0
    insurance_deduction: float = 0.0
    unpaid_leave_deduction: float = 0.0
    other_deductions: float = 0.0
    total_deductions: float = 0.0
    net_salary: float = 0.0
    status: PayslipStatus = PayslipStatus.GENERATED
    payment_method: str | None = None
    payment_reference: str | None = None
    paid_at: datetime | None = None


class PayslipResponse(PayslipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Incentive Schemas
# ---------------------------------------------------------
class EmployeeIncentiveBase(BaseModel):
    employee_id: UUID
    period_month: int
    period_year: int
    criterion_type: IncentiveCriterion
    target_value: float = 0.0
    achieved_value: float = 0.0
    rate_or_percentage: float = 0.0
    calculated_amount: float = 0.0
    status: IncentiveStatus = IncentiveStatus.PENDING
    notes: str | None = None


class EmployeeIncentiveCreate(EmployeeIncentiveBase):
    pass


class EmployeeIncentiveResponse(EmployeeIncentiveBase):
    id: UUID
    approved_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Performance Review Schemas
# ---------------------------------------------------------
class PerformanceReviewBase(BaseModel):
    employee_id: UUID
    review_cycle: ReviewCycle = ReviewCycle.QUARTERLY
    review_period: str
    clinical_skills_rating: float = 5.0
    patient_satisfaction_rating: float = 5.0
    punctuality_rating: float = 5.0
    teamwork_rating: float = 5.0
    protocol_adherence_rating: float = 5.0
    overall_rating: float = 5.0
    kpi_details_json: str | None = None
    strengths: str | None = None
    areas_of_improvement: str | None = None
    goals_next_period: str | None = None
    training_needs: str | None = None
    employee_feedback: str | None = None
    status: ReviewStatus = ReviewStatus.DRAFT


class PerformanceReviewCreate(PerformanceReviewBase):
    organization_id: UUID | None = None
    clinic_id: UUID
    reviewer_id: UUID | None = None


class PerformanceReviewUpdate(BaseModel):
    clinical_skills_rating: float | None = None
    patient_satisfaction_rating: float | None = None
    punctuality_rating: float | None = None
    teamwork_rating: float | None = None
    protocol_adherence_rating: float | None = None
    overall_rating: float | None = None
    kpi_details_json: str | None = None
    strengths: str | None = None
    areas_of_improvement: str | None = None
    goals_next_period: str | None = None
    training_needs: str | None = None
    employee_feedback: str | None = None
    status: ReviewStatus | None = None


class PerformanceReviewResponse(PerformanceReviewBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID
    reviewer_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Training & Credentialing Schemas
# ---------------------------------------------------------
class TrainingCourseBase(BaseModel):
    title: str = Field(..., max_length=200)
    provider: str = Field(..., max_length=160)
    course_type: CourseType = CourseType.CONTINUING_EDUCATION
    credits_hours: float = 1.0
    is_mandatory: bool = False
    validity_months: int = 12
    description: str | None = None


class TrainingCourseCreate(TrainingCourseBase):
    organization_id: UUID | None = None


class TrainingCourseResponse(TrainingCourseBase):
    id: UUID
    organization_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeTrainingRecordBase(BaseModel):
    employee_id: UUID
    course_id: UUID | None = None
    course_title: str
    completion_date: date
    expiry_date: date | None = None
    certificate_number: str | None = None
    certificate_url: str | None = None
    status: TrainingRecordStatus = TrainingRecordStatus.COMPLETED


class EmployeeTrainingRecordCreate(EmployeeTrainingRecordBase):
    pass


class EmployeeTrainingRecordResponse(EmployeeTrainingRecordBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Recruitment Schemas
# ---------------------------------------------------------
class JobOpeningBase(BaseModel):
    title: str = Field(..., max_length=160)
    department_id: UUID | None = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    open_positions: int = 1
    experience_years_min: int = 1
    status: JobStatus = JobStatus.OPEN
    description: str
    requirements: str | None = None


class JobOpeningCreate(JobOpeningBase):
    organization_id: UUID | None = None
    clinic_id: UUID | None = None


class JobOpeningUpdate(BaseModel):
    title: str | None = None
    department_id: UUID | None = None
    employment_type: EmploymentType | None = None
    open_positions: int | None = None
    experience_years_min: int | None = None
    status: JobStatus | None = None
    description: str | None = None
    requirements: str | None = None


class JobOpeningResponse(JobOpeningBase):
    id: UUID
    organization_id: UUID | None = None
    clinic_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobApplicantBase(BaseModel):
    job_opening_id: UUID
    full_name: str = Field(..., max_length=120)
    email: EmailStr
    phone: str = Field(..., max_length=32)
    resume_url: str | None = None
    qualification: str | None = None
    experience_years: float = 0.0
    current_stage: ApplicantStage = ApplicantStage.APPLIED
    notes: str | None = None


class JobApplicantCreate(JobApplicantBase):
    pass


class JobApplicantUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    resume_url: str | None = None
    qualification: str | None = None
    experience_years: float | None = None
    current_stage: ApplicantStage | None = None
    notes: str | None = None


class JobApplicantResponse(JobApplicantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewScheduleBase(BaseModel):
    applicant_id: UUID
    interviewer_id: UUID | None = None
    scheduled_at: datetime
    interview_type: InterviewType = InterviewType.TECHNICAL
    feedback_notes: str | None = None
    rating: float | None = None
    result: InterviewResult = InterviewResult.PENDING


class InterviewScheduleCreate(InterviewScheduleBase):
    pass


class InterviewScheduleUpdate(BaseModel):
    scheduled_at: datetime | None = None
    interview_type: InterviewType | None = None
    feedback_notes: str | None = None
    rating: float | None = None
    result: InterviewResult | None = None


class InterviewScheduleResponse(InterviewScheduleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Document Schemas
# ---------------------------------------------------------
class EmployeeDocumentBase(BaseModel):
    employee_id: UUID
    document_type: DocumentType
    title: str = Field(..., max_length=160)
    file_url: str = Field(..., max_length=255)
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"
    version: int = 1
    expiry_date: date | None = None
    is_verified: bool = False


class EmployeeDocumentCreate(EmployeeDocumentBase):
    pass


class EmployeeDocumentResponse(EmployeeDocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Dashboard & AI Workforce Schemas
# ---------------------------------------------------------
class HRDashboardMetricsResponse(BaseModel):
    total_headcount: int
    active_employees: int
    on_leave_employees: int
    today_scheduled: int
    today_present: int
    today_late: int
    attendance_rate: float
    pending_leaves: int
    current_month_payroll_total: float
    open_job_positions: int
    licenses_expiring_soon: int


class StaffingRecommendationItem(BaseModel):
    clinic_id: UUID
    date: date
    time_slot: str
    scheduled_chairs: int
    appointments_booked: int
    scheduled_clinicians: int
    recommended_clinicians: int
    status: str  # "OPTIMAL", "UNDERSTAFFED", "OVERSTAFFED"
    recommendation: str


class StaffingOptimizationResponse(BaseModel):
    analysis_period: str
    total_slots_analyzed: int
    understaffed_slots: int
    recommendations: list[StaffingRecommendationItem]


class ScheduleConflictItem(BaseModel):
    schedule_id: UUID
    employee_id: UUID
    employee_name: str
    conflict_type: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    description: str


class ScheduleConflictAuditResponse(BaseModel):
    total_conflicts: int
    conflicts: list[ScheduleConflictItem]


class LeaveConflictItem(BaseModel):
    clinic_id: UUID
    department_name: str
    overlapping_dates: str
    affected_employees: list[str]
    warning_level: str
    advice: str


class LeaveConflictDetectionResponse(BaseModel):
    conflicts_detected: int
    details: list[LeaveConflictItem]


class BurnoutRiskItem(BaseModel):
    employee_id: UUID
    employee_name: str
    designation: str
    overtime_hours_month: float
    consecutive_days_worked: int
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    key_factors: list[str]
    suggested_action: str


class BurnoutRiskAssessmentResponse(BaseModel):
    high_risk_count: int
    moderate_risk_count: int
    assessments: list[BurnoutRiskItem]


class TrainingComplianceItem(BaseModel):
    employee_id: UUID
    employee_name: str
    item_type: str  # "LICENSE_EXPIRY", "MANDATORY_COURSE_EXPIRED", "CE_CREDITS_SHORTAGE"
    title: str
    expiry_date: date | None = None
    days_remaining: int | None = None
    urgency: str  # "CRITICAL", "WARNING", "INFO"


class TrainingComplianceRecommendationResponse(BaseModel):
    total_compliance_alerts: int
    critical_alerts: int
    alerts: list[TrainingComplianceItem]
