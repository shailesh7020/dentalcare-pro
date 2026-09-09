from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.ai import (
    AIAuditLog,
    AIConfiguration,
    AIProviderType,
    AIRecommendation,
    AIRecommendationStatus,
)
from app.models.identity import Role, User
from app.schemas.ai import (
    AIAnalyticsInsightsResponse,
    AIAuditLogRead,
    AIConfigRead,
    AIConfigUpdate,
    AIRecommendationRead,
    AIRecommendationReview,
    AISearchRequest,
    AISearchResponse,
    BillingAuditRequest,
    BillingAuditResponse,
    ClinicalDocGenerateRequest,
    ClinicalDocResponse,
    InventoryForecastResponse,
    MissingDocAuditRequest,
    MissingDocAuditResponse,
    PatientSummaryRequest,
    PatientSummaryResponse,
    PrescriptionSuggestRequest,
    PrescriptionSuggestResponse,
    SchedulingRecommendationRequest,
    SchedulingSlotRecommendation,
    SOAPGenerateRequest,
    SOAPNoteDraft,
    SOAPSaveRequest,
    TreatmentSuggestionRequest,
    TreatmentSuggestionResponse,
)
from app.schemas.treatment import TreatmentDetail
from app.services.ai.analytics_service import AIBusinessAnalyticsService
from app.services.ai.billing_assistant_service import AIBillingAssistantService
from app.services.ai.clinical_assistant_service import AIClinicalAssistantService
from app.services.ai.documentation_service import AIDocumentationService
from app.services.ai.inventory_forecasting_service import AIInventoryForecastingService
from app.services.ai.prescription_assistant_service import AIPrescriptionAssistanceService
from app.services.ai.scheduling_assistant_service import AISchedulingAssistantService
from app.services.ai.search_service import AINaturalLanguageSearchService
from app.services.ai.soap_service import AISOAPNoteService
from app.services.treatment_service import TreatmentService

router = APIRouter(prefix="/ai", tags=["AI Clinical Assistant & Intelligent Automation"])

CLINICAL_ROLES = (
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.ASSISTANT,
)
ADMIN_ROLES = (
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
)
ALL_STAFF_ROLES = (
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.ASSISTANT,
    Role.RECEPTIONIST,
)


def _resolve_clinic_id(actor: User, requested_clinic_id: UUID | None = None) -> UUID:
    """Resolve and enforce clinic_id based on user tenancy."""
    if actor.role == Role.SUPER_ADMIN:
        if requested_clinic_id:
            return requested_clinic_id
        if actor.clinic_id:
            return actor.clinic_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="clinic_id is required for superadmin requests without assigned clinic",
        )
    if not actor.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any clinic",
        )
    if requested_clinic_id and requested_clinic_id != actor.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot query another clinic's AI data",
        )
    return actor.clinic_id


# ---------------------------------------------------------------------------
# AI Clinic Configuration
# ---------------------------------------------------------------------------


@router.get(
    "/config",
    response_model=AIConfigRead,
    summary="Get AI configuration for clinic",
)
async def get_ai_config(
    clinic_id: Annotated[UUID | None, Query()] = None,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> AIConfigRead:
    cid = _resolve_clinic_id(actor, clinic_id)
    stmt = select(AIConfiguration).where(AIConfiguration.clinic_id == cid)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()
    if not config:
        config = AIConfiguration(
            id=uuid4(),
            clinic_id=cid,
            provider_type=AIProviderType.MOCK,
            model_name="mock-clinical-v1",
            temperature=0.2,
            max_tokens=2048,
            clinical_guardrails_enabled=True,
            is_active=True,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return AIConfigRead.model_validate(config)


@router.put(
    "/config",
    response_model=AIConfigRead,
    summary="Update or set AI configuration for clinic",
)
async def update_ai_config(
    payload: AIConfigUpdate,
    clinic_id: Annotated[UUID | None, Query()] = None,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> AIConfigRead:
    cid = _resolve_clinic_id(actor, clinic_id)
    stmt = select(AIConfiguration).where(AIConfiguration.clinic_id == cid)
    res = await db.execute(stmt)
    config = res.scalar_one_or_none()

    if not config:
        config = AIConfiguration(
            id=uuid4(),
            clinic_id=cid,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.add(config)

    if payload.provider_type is not None:
        config.provider_type = payload.provider_type
    if payload.model_name is not None:
        config.model_name = payload.model_name
    if payload.api_base_url is not None:
        config.api_base_url = payload.api_base_url
    if payload.api_key is not None:
        config.api_key_encrypted = payload.api_key
    if payload.temperature is not None:
        config.temperature = payload.temperature
    if payload.max_tokens is not None:
        config.max_tokens = payload.max_tokens
    if payload.clinical_guardrails_enabled is not None:
        config.clinical_guardrails_enabled = payload.clinical_guardrails_enabled
    if payload.is_active is not None:
        config.is_active = payload.is_active

    config.updated_by = actor.id
    await db.commit()
    await db.refresh(config)
    return AIConfigRead.model_validate(config)


# ---------------------------------------------------------------------------
# Clinical Assistant (Summaries & Missing Docs)
# ---------------------------------------------------------------------------


@router.post(
    "/assistant/summary",
    response_model=PatientSummaryResponse,
    summary="Generate AI patient clinical summary and risk alerts",
)
async def generate_patient_summary(
    payload: PatientSummaryRequest,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientSummaryResponse:
    _resolve_clinic_id(actor)
    service = AIClinicalAssistantService(db)
    return await service.summarize_patient_history(payload, actor)


@router.post(
    "/assistant/missing-docs",
    response_model=MissingDocAuditResponse,
    summary="Audit patient clinical records for missing documentation",
)
async def audit_missing_documentation(
    payload: MissingDocAuditRequest,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> MissingDocAuditResponse:
    cid = _resolve_clinic_id(actor)
    service = AIClinicalAssistantService(db)
    return await service.detect_missing_documentation(payload.patient_id, cid)


# ---------------------------------------------------------------------------
# SOAP Note Generation & Review Save
# ---------------------------------------------------------------------------


@router.post(
    "/soap/generate",
    response_model=SOAPNoteDraft,
    summary="Generate clinical SOAP note draft",
)
async def generate_soap_note(
    payload: SOAPGenerateRequest,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SOAPNoteDraft:
    cid = _resolve_clinic_id(actor)
    service = AISOAPNoteService(db)
    return await service.generate_soap_draft(cid, payload, actor.id)


@router.post(
    "/soap/save",
    response_model=TreatmentDetail,
    summary="Clinician review and save of SOAP note into clinical records",
)
async def save_soap_note(
    payload: SOAPSaveRequest,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    cid = _resolve_clinic_id(actor)
    service = AISOAPNoteService(db)
    trt = await service.save_soap_to_treatment(cid, payload, actor.id)
    trt_svc = TreatmentService(db)
    return await trt_svc.get_treatment(cid, trt.id)


# ---------------------------------------------------------------------------
# Prescription & Treatment Suggestions
# ---------------------------------------------------------------------------


@router.post(
    "/prescriptions/suggest",
    response_model=PrescriptionSuggestResponse,
    summary="Suggest diagnosis-driven medications and allergy checks",
)
async def suggest_prescriptions(
    payload: PrescriptionSuggestRequest,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionSuggestResponse:
    cid = _resolve_clinic_id(actor)
    service = AIPrescriptionAssistanceService(db)
    return await service.suggest_medications(cid, payload, actor.id)


@router.post(
    "/treatment-suggestions",
    response_model=TreatmentSuggestionResponse,
    summary="Generate AI treatment plan suggestions and recall intervals",
)
async def suggest_treatment_plan(
    payload: TreatmentSuggestionRequest,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> TreatmentSuggestionResponse:
    cid = _resolve_clinic_id(actor)
    service = AIPrescriptionAssistanceService(db)
    return await service.suggest_treatment_plan(cid, payload, actor.id)


# ---------------------------------------------------------------------------
# Clinical Documentation (Referrals, Certificates, Instructions)
# ---------------------------------------------------------------------------


@router.post(
    "/documents/generate",
    response_model=ClinicalDocResponse,
    summary="Generate clinical documentation (referrals, certificates, post-op instructions)",
)
async def generate_clinical_document(
    payload: ClinicalDocGenerateRequest,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> ClinicalDocResponse:
    cid = _resolve_clinic_id(actor)
    service = AIDocumentationService(db)
    return await service.generate_document(cid, payload, actor.id)


# ---------------------------------------------------------------------------
# Billing Assistant
# ---------------------------------------------------------------------------


@router.post(
    "/billing/audit",
    response_model=BillingAuditResponse,
    summary="Audit unbilled procedures and consumed materials",
)
async def audit_billing(
    payload: BillingAuditRequest,
    actor: User = Depends(require_roles(*ALL_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> BillingAuditResponse:
    cid = _resolve_clinic_id(actor)
    service = AIBillingAssistantService(db)
    return await service.audit_unbilled_items(cid, payload, actor.id)


# ---------------------------------------------------------------------------
# Scheduling Assistant
# ---------------------------------------------------------------------------


@router.post(
    "/scheduling/recommend",
    response_model=SchedulingSlotRecommendation,
    summary="Recommend procedure duration and optimal scheduling slots",
)
async def recommend_scheduling(
    payload: SchedulingRecommendationRequest,
    actor: User = Depends(require_roles(*ALL_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SchedulingSlotRecommendation:
    cid = _resolve_clinic_id(actor)
    service = AISchedulingAssistantService(db)
    return await service.recommend_slot(cid, payload)


# ---------------------------------------------------------------------------
# Inventory Forecasting
# ---------------------------------------------------------------------------


@router.get(
    "/inventory/forecast",
    response_model=InventoryForecastResponse,
    summary="Forecast stock depletion dates and reorder quantities",
)
async def forecast_inventory(
    clinic_id: Annotated[UUID | None, Query()] = None,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> InventoryForecastResponse:
    cid = _resolve_clinic_id(actor, clinic_id)
    service = AIInventoryForecastingService(db)
    return await service.forecast_demand(cid)


# ---------------------------------------------------------------------------
# Business Analytics Insights
# ---------------------------------------------------------------------------


@router.get(
    "/analytics/insights",
    response_model=AIAnalyticsInsightsResponse,
    summary="Generate natural language business intelligence and revenue insights",
)
async def get_practice_insights(
    clinic_id: Annotated[UUID | None, Query()] = None,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> AIAnalyticsInsightsResponse:
    cid = _resolve_clinic_id(actor, clinic_id)
    service = AIBusinessAnalyticsService(db)
    return await service.generate_insights(cid)


# ---------------------------------------------------------------------------
# Natural Language Search
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    response_model=AISearchResponse,
    summary="Natural language clinical search with multi-tenant isolation",
)
async def search_clinical_data(
    payload: AISearchRequest,
    actor: User = Depends(require_roles(*ALL_STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> AISearchResponse:
    cid = _resolve_clinic_id(actor)
    service = AINaturalLanguageSearchService(db)
    return await service.search_natural_language(cid, payload, actor)


# ---------------------------------------------------------------------------
# AI Recommendations Queue & Human Clinician Review
# ---------------------------------------------------------------------------


@router.get(
    "/recommendations",
    response_model=list[AIRecommendationRead],
    summary="List pending or historical AI recommendations for clinic",
)
async def list_recommendations(
    clinic_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[AIRecommendationStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    actor: User = Depends(require_roles(*CLINICAL_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[AIRecommendationRead]:
    cid = _resolve_clinic_id(actor, clinic_id)
    query = (
        select(AIRecommendation)
        .where(AIRecommendation.clinic_id == cid)
        .order_by(desc(AIRecommendation.created_at))
        .limit(limit)
    )
    if status:
        query = query.where(AIRecommendation.status == status)

    res = await db.execute(query)
    recs = res.scalars().all()
    return [AIRecommendationRead.model_validate(r) for r in recs]


@router.post(
    "/recommendations/{recommendation_id}/review",
    response_model=AIRecommendationRead,
    summary="Clinician review (accept/reject/modify) an AI recommendation",
)
async def review_recommendation(
    recommendation_id: UUID,
    payload: AIRecommendationReview,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST)),
    db: AsyncSession = Depends(get_db),
) -> AIRecommendationRead:
    rec = await db.get(AIRecommendation, recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    _resolve_clinic_id(actor, rec.clinic_id)

    rec.status = payload.status
    rec.reviewed_by_id = actor.id
    rec.reviewed_at = datetime.now(UTC)
    if payload.clinician_feedback:
        rec.clinician_feedback = payload.clinician_feedback
    if payload.final_content:
        rec.final_content = payload.final_content

    rec.updated_by = actor.id
    await db.commit()
    await db.refresh(rec)
    return AIRecommendationRead.model_validate(rec)


# ---------------------------------------------------------------------------
# AI Audit Logs
# ---------------------------------------------------------------------------


@router.get(
    "/audit-logs",
    response_model=list[AIAuditLogRead],
    summary="Query AI inference audit logs for clinic",
)
async def list_ai_audit_logs(
    clinic_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[AIAuditLogRead]:
    cid = _resolve_clinic_id(actor, clinic_id)
    stmt = (
        select(AIAuditLog)
        .where(AIAuditLog.clinic_id == cid)
        .order_by(desc(AIAuditLog.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [AIAuditLogRead.model_validate(lg) for lg in logs]
