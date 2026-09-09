from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.insurance import (
    ClaimCompletenessAuditResponse,
    ClaimCreate,
    ClaimDetail,
    ClaimRead,
    ClaimsReportResponse,
    ClaimStatusUpdate,
    CodingSuggestionResponse,
    InsuranceCoverageRuleCreate,
    InsuranceCoverageRuleRead,
    InsuranceDashboardStats,
    InsurancePlanCreate,
    InsurancePlanRead,
    InsurancePlanUpdate,
    InsuranceProviderCreate,
    InsuranceProviderDetail,
    InsuranceProviderRead,
    InsuranceProviderUpdate,
    PatientInsurancePolicyCreate,
    PatientInsurancePolicyRead,
    PatientInsurancePolicyUpdate,
    PaymentReconciliationCreate,
    PaymentReconciliationRead,
    PolicyVerificationRequest,
    PreAuthCreate,
    PreAuthRead,
    PreAuthStatusUpdate,
    ProviderPerformanceResponse,
    RejectionAnalysisResponse,
)
from app.services.ai.insurance_assistant_service import InsuranceAssistantService
from app.services.insurance_service import InsuranceService

router = APIRouter(prefix="/insurance", tags=["Insurance, Claims & TPA Management"])

STAFF_ROLES = (
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
)
ADMIN_ROLES = (
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
)


def _resolve_clinic_id(actor: User, requested_clinic_id: UUID | None = None) -> UUID:
    if actor.role == Role.SUPER_ADMIN:
        if requested_clinic_id:
            return requested_clinic_id
        if actor.clinic_id:
            return actor.clinic_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Superadmin must provide clinic_id context",
        )
    if not actor.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to a valid clinic",
        )
    return actor.clinic_id


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=InsuranceDashboardStats)
async def get_insurance_dashboard(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsuranceDashboardStats:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_dashboard_stats(c_id)


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
@router.get("/providers", response_model=list[InsuranceProviderRead])
async def list_providers(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[InsuranceProviderRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_providers(c_id, is_active, search, limit, offset)


@router.post("/providers", response_model=InsuranceProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: InsuranceProviderCreate,
    current_user: Annotated[User, Depends(require_roles(*ADMIN_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsuranceProviderRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_provider(c_id, payload, created_by=current_user.id)


@router.get("/providers/{provider_id}", response_model=InsuranceProviderDetail)
async def get_provider(
    provider_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsuranceProviderDetail:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_provider(c_id, provider_id)


@router.put("/providers/{provider_id}", response_model=InsuranceProviderRead)
async def update_provider(
    provider_id: UUID,
    payload: InsuranceProviderUpdate,
    current_user: Annotated[User, Depends(require_roles(*ADMIN_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsuranceProviderRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.update_provider(c_id, provider_id, payload, updated_by=current_user.id)


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
@router.get("/plans", response_model=list[InsurancePlanRead])
async def list_plans(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[InsurancePlanRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_plans(c_id, provider_id, is_active, limit, offset)


@router.post("/plans", response_model=InsurancePlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: InsurancePlanCreate,
    current_user: Annotated[User, Depends(require_roles(*ADMIN_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsurancePlanRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_plan(c_id, payload, created_by=current_user.id)


@router.get("/plans/{plan_id}", response_model=InsurancePlanRead)
async def get_plan(
    plan_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsurancePlanRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_plan(c_id, plan_id)


@router.put("/plans/{plan_id}", response_model=InsurancePlanRead)
async def update_plan(
    plan_id: UUID,
    payload: InsurancePlanUpdate,
    current_user: Annotated[User, Depends(require_roles(*ADMIN_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsurancePlanRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.update_plan(c_id, plan_id, payload, updated_by=current_user.id)


@router.get("/plans/{plan_id}/coverage-rules", response_model=list[InsuranceCoverageRuleRead])
async def list_coverage_rules(
    plan_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> list[InsuranceCoverageRuleRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.repo.list_coverage_rules(c_id, plan_id)


@router.post("/plans/{plan_id}/coverage-rules", response_model=InsuranceCoverageRuleRead, status_code=status.HTTP_201_CREATED)
async def create_coverage_rule(
    plan_id: UUID,
    payload: InsuranceCoverageRuleCreate,
    current_user: Annotated[User, Depends(require_roles(*ADMIN_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> InsuranceCoverageRuleRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.repo.create_coverage_rule(c_id, payload, created_by=current_user.id)


# ---------------------------------------------------------------------------
# Patient Policies
# ---------------------------------------------------------------------------
@router.get("/policies", response_model=list[PatientInsurancePolicyRead])
async def list_patient_policies(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: UUID | None = Query(None),
    policy_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[PatientInsurancePolicyRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_patient_policies(c_id, patient_id, policy_status, limit, offset)


@router.post("/policies", response_model=PatientInsurancePolicyRead, status_code=status.HTTP_201_CREATED)
async def create_patient_policy(
    payload: PatientInsurancePolicyCreate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PatientInsurancePolicyRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_policy(c_id, payload, created_by=current_user.id)


@router.get("/policies/{policy_id}", response_model=PatientInsurancePolicyRead)
async def get_patient_policy(
    policy_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PatientInsurancePolicyRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_policy(c_id, policy_id)


@router.put("/policies/{policy_id}", response_model=PatientInsurancePolicyRead)
async def update_patient_policy(
    policy_id: UUID,
    payload: PatientInsurancePolicyUpdate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PatientInsurancePolicyRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.update_policy(c_id, policy_id, payload, updated_by=current_user.id)


@router.post("/policies/{policy_id}/verify", response_model=PatientInsurancePolicyRead)
async def verify_patient_policy(
    policy_id: UUID,
    payload: PolicyVerificationRequest,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PatientInsurancePolicyRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    payload.verified_by = payload.verified_by or current_user.id
    return await service.verify_policy(c_id, policy_id, payload)


# ---------------------------------------------------------------------------
# Pre-Authorizations
# ---------------------------------------------------------------------------
@router.get("/preauth", response_model=list[PreAuthRead])
async def list_preauthorizations(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: UUID | None = Query(None),
    preauth_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[PreAuthRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_preauths(c_id, patient_id, preauth_status, limit, offset)


@router.post("/preauth", response_model=PreAuthRead, status_code=status.HTTP_201_CREATED)
async def create_preauthorization(
    payload: PreAuthCreate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PreAuthRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_preauth(c_id, payload, created_by=current_user.id)


@router.get("/preauth/{preauth_id}", response_model=PreAuthRead)
async def get_preauthorization(
    preauth_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PreAuthRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_preauth(c_id, preauth_id)


@router.put("/preauth/{preauth_id}/status", response_model=PreAuthRead)
async def update_preauthorization_status(
    preauth_id: UUID,
    payload: PreAuthStatusUpdate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PreAuthRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.update_preauth_status(c_id, preauth_id, payload, updated_by=current_user.id)


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------
@router.get("/claims", response_model=list[ClaimRead])
async def list_claims(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: UUID | None = Query(None),
    claim_status: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[ClaimRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_claims(c_id, patient_id, claim_status, search, limit, offset)


@router.post("/claims", response_model=ClaimDetail, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> ClaimDetail:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_claim(c_id, payload, created_by=current_user.id)


@router.get("/claims/{claim_id}", response_model=ClaimDetail)
async def get_claim(
    claim_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> ClaimDetail:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.get_claim(c_id, claim_id)


@router.put("/claims/{claim_id}/status", response_model=ClaimDetail)
async def update_claim_status(
    claim_id: UUID,
    payload: ClaimStatusUpdate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> ClaimDetail:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.update_claim_status(c_id, claim_id, payload, updated_by=current_user.id)


# ---------------------------------------------------------------------------
# Reconciliations
# ---------------------------------------------------------------------------
@router.get("/reconciliations", response_model=list[PaymentReconciliationRead])
async def list_reconciliations(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    claim_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    clinic_id: UUID | None = Query(None),
) -> list[PaymentReconciliationRead]:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.list_reconciliations(c_id, claim_id, limit, offset)


@router.post("/reconciliations", response_model=PaymentReconciliationRead, status_code=status.HTTP_201_CREATED)
async def create_reconciliation(
    payload: PaymentReconciliationCreate,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> PaymentReconciliationRead:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.create_reconciliation(c_id, payload, created_by=current_user.id)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@router.get("/reports/claims", response_model=ClaimsReportResponse)
async def get_claims_report(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    claim_status: str | None = Query(None, alias="status"),
    clinic_id: UUID | None = Query(None),
) -> ClaimsReportResponse:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.generate_claims_report(c_id, start_date, end_date, claim_status)


@router.get("/reports/provider-performance", response_model=ProviderPerformanceResponse)
async def get_provider_performance_report(
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
    db: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: UUID | None = Query(None),
) -> ProviderPerformanceResponse:
    c_id = _resolve_clinic_id(current_user, clinic_id)
    service = InsuranceService(db)
    return await service.generate_provider_performance_report(c_id)


# ---------------------------------------------------------------------------
# AI Insurance Assistant
# ---------------------------------------------------------------------------
class AuditCompletenessRequest(BaseModel):
    claim_id: UUID
    procedure_codes: list[str] = []
    attached_document_types: list[str] = []
    patient_notes: str | None = None


class SuggestCodingRequest(BaseModel):
    procedure_descriptions: list[str] = []


class AnalyzeRejectionRequest(BaseModel):
    claim_id: UUID
    denial_code: str | None = None
    denial_reason: str | None = None


@router.post("/ai/audit-completeness", response_model=ClaimCompletenessAuditResponse)
async def audit_claim_completeness(
    payload: AuditCompletenessRequest,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
) -> ClaimCompletenessAuditResponse:
    ai_service = InsuranceAssistantService()
    return await ai_service.audit_claim_completeness(
        claim_id=payload.claim_id,
        procedure_codes=payload.procedure_codes,
        attached_document_types=payload.attached_document_types,
        patient_notes=payload.patient_notes,
    )


@router.post("/ai/suggest-coding", response_model=CodingSuggestionResponse)
async def suggest_coding(
    payload: SuggestCodingRequest,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
) -> CodingSuggestionResponse:
    ai_service = InsuranceAssistantService()
    return await ai_service.suggest_procedure_coding(payload.procedure_descriptions)


@router.post("/ai/analyze-rejection", response_model=RejectionAnalysisResponse)
async def analyze_rejection(
    payload: AnalyzeRejectionRequest,
    current_user: Annotated[User, Depends(require_roles(*STAFF_ROLES))],
) -> RejectionAnalysisResponse:
    ai_service = InsuranceAssistantService()
    return await ai_service.analyze_rejection(
        claim_id=payload.claim_id,
        denial_code=payload.denial_code,
        denial_reason=payload.denial_reason,
    )
