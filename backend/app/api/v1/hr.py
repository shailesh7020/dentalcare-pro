from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.hr import (
    ApplicantStage,
    EmployeeStatus,
    JobStatus,
    LeaveStatus,
)
from app.schemas.hr import (
    AttendanceRecordResponse,
    BurnoutRiskAssessmentResponse,
    ClockInRequest,
    ClockOutRequest,
    EmployeeCreate,
    EmployeeDocumentCreate,
    EmployeeDocumentResponse,
    EmployeeIncentiveCreate,
    EmployeeIncentiveResponse,
    EmployeeResponse,
    EmployeeTrainingRecordCreate,
    EmployeeTrainingRecordResponse,
    EmployeeUpdate,
    HRDashboardMetricsResponse,
    InterviewScheduleCreate,
    InterviewScheduleResponse,
    JobApplicantCreate,
    JobApplicantResponse,
    JobOpeningCreate,
    JobOpeningResponse,
    LeaveActionRequest,
    LeaveAllocationResponse,
    LeaveConflictDetectionResponse,
    LeaveRequestCreate,
    LeaveRequestResponse,
    PayrollRunCreate,
    PayrollRunResponse,
    PayslipResponse,
    PerformanceReviewCreate,
    PerformanceReviewResponse,
    ScheduleConflictAuditResponse,
    StaffingOptimizationResponse,
    StaffScheduleCreate,
    StaffScheduleResponse,
    TrainingComplianceRecommendationResponse,
    TrainingCourseCreate,
    TrainingCourseResponse,
    WorkShiftCreate,
    WorkShiftResponse,
)
from app.services.ai.workforce_ai_service import WorkforceAIService
from app.services.hr_service import HRService

router = APIRouter(prefix="/hr", tags=["Human Resources & Workforce Management"])


# ---------------------------------------------------------
# Dashboard Metrics
# ---------------------------------------------------------
@router.get("/dashboard", response_model=HRDashboardMetricsResponse)
async def get_hr_dashboard(
    clinic_id: UUID | None = None,
    organization_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> HRDashboardMetricsResponse:
    service = HRService(db)
    metrics = await service.get_dashboard_metrics(clinic_id, organization_id)
    return HRDashboardMetricsResponse(**metrics)


# ---------------------------------------------------------
# Employee Management
# ---------------------------------------------------------
@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    service = HRService(db)
    return await service.create_employee(payload)


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    organization_id: UUID | None = None,
    clinic_id: UUID | None = None,
    department_id: UUID | None = None,
    status: EmployeeStatus | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeResponse]:
    service = HRService(db)
    return await service.list_employees(
        organization_id=organization_id,
        clinic_id=clinic_id,
        department_id=department_id,
        status_filter=status,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    service = HRService(db)
    return await service.get_employee(employee_id)


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    service = HRService(db)
    return await service.update_employee(employee_id, payload)


# ---------------------------------------------------------
# Shifts & Scheduling
# ---------------------------------------------------------
@router.post("/shifts", response_model=WorkShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_work_shift(
    payload: WorkShiftCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkShiftResponse:
    service = HRService(db)
    return await service.create_work_shift(payload.model_dump())


@router.get("/shifts", response_model=list[WorkShiftResponse])
async def list_work_shifts(
    organization_id: UUID | None = None,
    clinic_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[WorkShiftResponse]:
    service = HRService(db)
    return await service.list_work_shifts(organization_id, clinic_id)


@router.post("/schedules", response_model=StaffScheduleResponse, status_code=status.HTTP_201_CREATED)
async def schedule_staff(
    payload: StaffScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> StaffScheduleResponse:
    service = HRService(db)
    return await service.schedule_staff(payload)


@router.get("/schedules", response_model=list[StaffScheduleResponse])
async def list_schedules(
    clinic_id: UUID,
    start_date: date,
    end_date: date,
    employee_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[StaffScheduleResponse]:
    service = HRService(db)
    return await service.list_schedules(clinic_id, start_date, end_date, employee_id)


# ---------------------------------------------------------
# Attendance
# ---------------------------------------------------------
@router.post("/attendance/clock-in", response_model=AttendanceRecordResponse)
async def clock_in(
    payload: ClockInRequest,
    db: AsyncSession = Depends(get_db),
) -> AttendanceRecordResponse:
    service = HRService(db)
    return await service.clock_in(
        clinic_id=payload.clinic_id,
        employee_id=payload.employee_id,
        entry_method=payload.entry_method,
        notes=payload.notes,
    )


@router.post("/attendance/clock-out", response_model=AttendanceRecordResponse)
async def clock_out(
    employee_id: UUID,
    payload: ClockOutRequest,
    db: AsyncSession = Depends(get_db),
) -> AttendanceRecordResponse:
    service = HRService(db)
    return await service.clock_out(employee_id=employee_id, notes=payload.notes)


@router.get("/attendance", response_model=list[AttendanceRecordResponse])
async def list_attendance(
    clinic_id: UUID,
    record_date: date | None = None,
    employee_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceRecordResponse]:
    service = HRService(db)
    target_date = record_date or datetime.now(UTC).date()
    return await service.list_attendance(clinic_id, target_date, employee_id)


# ---------------------------------------------------------
# Leave Management
# ---------------------------------------------------------
@router.get("/leave/allocations", response_model=list[LeaveAllocationResponse])
async def get_leave_allocations(
    employee_id: UUID,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[LeaveAllocationResponse]:
    service = HRService(db)
    target_year = year or datetime.now(UTC).date().year
    return await service.get_leave_allocations(employee_id, target_year)


@router.post("/leave/requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_leave_request(
    payload: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
) -> LeaveRequestResponse:
    service = HRService(db)
    return await service.request_leave(payload)


@router.get("/leave/requests", response_model=list[LeaveRequestResponse])
async def list_leave_requests(
    clinic_id: UUID | None = None,
    employee_id: UUID | None = None,
    status: LeaveStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[LeaveRequestResponse]:
    service = HRService(db)
    return await service.list_leave_requests(clinic_id, employee_id, status)


@router.post("/leave/requests/{request_id}/action", response_model=LeaveRequestResponse)
async def process_leave_action(
    request_id: UUID,
    payload: LeaveActionRequest,
    reviewer_user_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> LeaveRequestResponse:
    service = HRService(db)
    # Default dummy user id if direct call without auth token
    user_id = reviewer_user_id or UUID("00000000-0000-0000-0000-000000000001")
    return await service.process_leave_action(request_id, user_id, payload)


# ---------------------------------------------------------
# Payroll Management
# ---------------------------------------------------------
@router.post("/payroll/runs", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
async def generate_payroll_run(
    payload: PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
) -> PayrollRunResponse:
    service = HRService(db)
    return await service.generate_payroll_run(payload)


@router.get("/payroll/runs", response_model=list[PayrollRunResponse])
async def list_payroll_runs(
    organization_id: UUID | None = None,
    clinic_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PayrollRunResponse]:
    service = HRService(db)
    return await service.list_payroll_runs(organization_id, clinic_id)


@router.get("/payroll/runs/{run_id}", response_model=PayrollRunResponse)
async def get_payroll_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PayrollRunResponse:
    service = HRService(db)
    return await service.get_payroll_run(run_id)


@router.get("/payroll/runs/{run_id}/payslips", response_model=list[PayslipResponse])
async def list_payslips_for_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PayslipResponse]:
    service = HRService(db)
    return await service.list_payslips_for_run(run_id)


@router.get("/payroll/employees/{employee_id}/payslips", response_model=list[PayslipResponse])
async def list_payslips_for_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PayslipResponse]:
    service = HRService(db)
    return await service.list_payslips_for_employee(employee_id)


# ---------------------------------------------------------
# Incentives
# ---------------------------------------------------------
@router.post("/incentives", response_model=EmployeeIncentiveResponse, status_code=status.HTTP_201_CREATED)
async def create_incentive(
    payload: EmployeeIncentiveCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeIncentiveResponse:
    service = HRService(db)
    return await service.repo.create_incentive(payload.model_dump())


@router.get("/incentives", response_model=list[EmployeeIncentiveResponse])
async def list_incentives(
    employee_id: UUID | None = None,
    month: int | None = None,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeIncentiveResponse]:
    service = HRService(db)
    return await service.repo.list_incentives(employee_id, month, year)


# ---------------------------------------------------------
# Performance Management
# ---------------------------------------------------------
@router.post("/performance", response_model=PerformanceReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_performance_review(
    payload: PerformanceReviewCreate,
    db: AsyncSession = Depends(get_db),
) -> PerformanceReviewResponse:
    service = HRService(db)
    return await service.create_performance_review(payload)


@router.get("/performance", response_model=list[PerformanceReviewResponse])
async def list_performance_reviews(
    clinic_id: UUID | None = None,
    employee_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PerformanceReviewResponse]:
    service = HRService(db)
    return await service.list_performance_reviews(clinic_id, employee_id)


# ---------------------------------------------------------
# Training & Doctor Credentialing
# ---------------------------------------------------------
@router.post("/training/courses", response_model=TrainingCourseResponse, status_code=status.HTTP_201_CREATED)
async def create_training_course(
    payload: TrainingCourseCreate,
    db: AsyncSession = Depends(get_db),
) -> TrainingCourseResponse:
    service = HRService(db)
    return await service.create_training_course(payload.model_dump())


@router.get("/training/courses", response_model=list[TrainingCourseResponse])
async def list_training_courses(
    organization_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TrainingCourseResponse]:
    service = HRService(db)
    return await service.list_training_courses(organization_id)


@router.post("/training/records", response_model=EmployeeTrainingRecordResponse, status_code=status.HTTP_201_CREATED)
async def log_training_record(
    payload: EmployeeTrainingRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeTrainingRecordResponse:
    service = HRService(db)
    return await service.log_training_record(payload.model_dump())


@router.get("/training/employees/{employee_id}", response_model=list[EmployeeTrainingRecordResponse])
async def list_employee_training_records(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeTrainingRecordResponse]:
    service = HRService(db)
    return await service.list_employee_training_records(employee_id)


# ---------------------------------------------------------
# Recruitment
# ---------------------------------------------------------
@router.post("/recruitment/openings", response_model=JobOpeningResponse, status_code=status.HTTP_201_CREATED)
async def create_job_opening(
    payload: JobOpeningCreate,
    db: AsyncSession = Depends(get_db),
) -> JobOpeningResponse:
    service = HRService(db)
    return await service.create_job_opening(payload.model_dump())


@router.get("/recruitment/openings", response_model=list[JobOpeningResponse])
async def list_job_openings(
    organization_id: UUID | None = None,
    clinic_id: UUID | None = None,
    status: JobStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[JobOpeningResponse]:
    service = HRService(db)
    return await service.list_job_openings(organization_id, clinic_id, status)


@router.post("/recruitment/applicants", response_model=JobApplicantResponse, status_code=status.HTTP_201_CREATED)
async def create_job_applicant(
    payload: JobApplicantCreate,
    db: AsyncSession = Depends(get_db),
) -> JobApplicantResponse:
    service = HRService(db)
    return await service.create_job_applicant(payload.model_dump())


@router.get("/recruitment/applicants", response_model=list[JobApplicantResponse])
async def list_job_applicants(
    job_opening_id: UUID | None = None,
    stage: ApplicantStage | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[JobApplicantResponse]:
    service = HRService(db)
    return await service.list_job_applicants(job_opening_id, stage)


@router.post("/recruitment/interviews", response_model=InterviewScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_schedule(
    payload: InterviewScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> InterviewScheduleResponse:
    service = HRService(db)
    return await service.create_interview_schedule(payload.model_dump())


@router.get("/recruitment/applicants/{applicant_id}/interviews", response_model=list[InterviewScheduleResponse])
async def list_interview_schedules(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[InterviewScheduleResponse]:
    service = HRService(db)
    return await service.list_interview_schedules(applicant_id)


# ---------------------------------------------------------
# Employee Documents
# ---------------------------------------------------------
@router.post("/documents", response_model=EmployeeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_employee_document(
    payload: EmployeeDocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeDocumentResponse:
    service = HRService(db)
    return await service.create_employee_document(payload.model_dump())


@router.get("/documents/employees/{employee_id}", response_model=list[EmployeeDocumentResponse])
async def list_employee_documents(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeDocumentResponse]:
    service = HRService(db)
    return await service.list_employee_documents(employee_id)


# ---------------------------------------------------------
# Employee Self-Service (ESS)
# ---------------------------------------------------------
@router.get("/me/profile", response_model=EmployeeResponse)
async def get_my_profile(
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    service = HRService(db)
    emp = await service.repo.get_employee_by_user_id(user_id)
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employee profile found for user")
    return emp


# ---------------------------------------------------------
# AI Workforce Assistant
# ---------------------------------------------------------
@router.get("/ai/staffing-recommendations", response_model=StaffingOptimizationResponse)
async def get_ai_staffing_recommendations(
    clinic_id: UUID,
    target_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> StaffingOptimizationResponse:
    ai_service = WorkforceAIService(db)
    dt = target_date or datetime.now(UTC).date()
    return await ai_service.get_staffing_recommendations(clinic_id, dt)


@router.get("/ai/schedule-conflicts", response_model=ScheduleConflictAuditResponse)
async def audit_ai_schedule_conflicts(
    clinic_id: UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
) -> ScheduleConflictAuditResponse:
    ai_service = WorkforceAIService(db)
    return await ai_service.audit_schedule_conflicts(clinic_id, start_date, end_date)


@router.get("/ai/leave-conflicts", response_model=LeaveConflictDetectionResponse)
async def detect_ai_leave_conflicts(
    clinic_id: UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
) -> LeaveConflictDetectionResponse:
    ai_service = WorkforceAIService(db)
    return await ai_service.detect_leave_conflicts(clinic_id, start_date, end_date)


@router.get("/ai/burnout-risks", response_model=BurnoutRiskAssessmentResponse)
async def assess_ai_burnout_risks(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BurnoutRiskAssessmentResponse:
    ai_service = WorkforceAIService(db)
    return await ai_service.assess_burnout_risks(clinic_id)


@router.get("/ai/training-compliance", response_model=TrainingComplianceRecommendationResponse)
async def audit_ai_training_compliance(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TrainingComplianceRecommendationResponse:
    ai_service = WorkforceAIService(db)
    return await ai_service.audit_training_compliance(clinic_id)
