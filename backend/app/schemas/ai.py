from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai import AIProviderType, AIRecommendationStatus


class AIConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    provider_type: str
    model_name: str
    api_base_url: str | None = None
    temperature: float
    max_tokens: int
    clinical_guardrails_enabled: bool
    is_active: bool


class AIConfigUpdate(BaseModel):
    provider_type: AIProviderType | None = None
    model_name: str | None = None
    api_base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(None, ge=256, le=8192)
    clinical_guardrails_enabled: bool | None = None
    is_active: bool | None = None


class RiskSeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskAlert(BaseModel):
    category: str
    severity: RiskSeverity
    title: str
    details: str


class PatientSummaryRequest(BaseModel):
    patient_id: UUID


class PatientSummaryResponse(BaseModel):
    patient_id: UUID
    patient_name: str
    summary_text: str
    risk_alerts: list[RiskAlert] = []
    previous_treatments_summary: str
    active_prescriptions_summary: str
    recommended_recall_months: int = 6
    missing_documentation_alerts: list[str] = []
    generated_at: datetime


class MissingDocAuditRequest(BaseModel):
    patient_id: UUID


class MissingDocAuditResponse(BaseModel):
    patient_id: UUID
    missing_items: list[str] = []
    unbilled_procedures: list[str] = []
    unsigned_consents: list[str] = []


class SOAPGenerateRequest(BaseModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    clinician_notes: str | None = None


class SOAPNoteDraft(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    safety_disclaimer: str = (
        "AI-generated clinical draft. Clinician must review and edit before finalizing."
    )


class SOAPSaveRequest(BaseModel):
    treatment_id: UUID
    subjective: str
    objective: str
    assessment: str
    plan: str


class ClinicalDocType(StrEnum):
    REFERRAL_LETTER = "REFERRAL_LETTER"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    POST_OP_INSTRUCTIONS = "POST_OP_INSTRUCTIONS"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    TREATMENT_PLAN_PRESENTATION = "TREATMENT_PLAN_PRESENTATION"


class ClinicalDocGenerateRequest(BaseModel):
    patient_id: UUID
    document_type: ClinicalDocType
    treatment_id: UUID | None = None
    recipient_doctor: str | None = None
    custom_notes: str | None = None


class ClinicalDocResponse(BaseModel):
    document_type: ClinicalDocType
    title: str
    formatted_content: str
    metadata: dict[str, Any] = {}
    disclaimer: str = "Clinically generated advisory draft. Requires doctor verification."


class PrescriptionSuggestRequest(BaseModel):
    patient_id: UUID
    diagnosis: str
    treatment_id: UUID | None = None


class PrescriptionSuggestionItem(BaseModel):
    medicine_name: str
    generic_name: str | None = None
    dosage: str
    frequency: str
    duration: str
    instructions: str
    rationale: str


class PrescriptionSuggestResponse(BaseModel):
    suggested_items: list[PrescriptionSuggestionItem] = []
    allergy_warnings: list[str] = []
    interaction_warnings: list[str] = []
    disclaimer: str = (
        "Advisory medication recommendations only. Clinician verification mandatory."
    )


class TreatmentOption(BaseModel):
    title: str
    procedure_code: str | None = None
    description: str
    pros: list[str] = []
    cons: list[str] = []
    estimated_visits: int = 1
    recall_interval_days: int = 180


class TreatmentSuggestionRequest(BaseModel):
    patient_id: UUID
    tooth_number: str | None = None
    chief_complaint: str


class TreatmentSuggestionResponse(BaseModel):
    primary_recommendation: TreatmentOption
    alternative_options: list[TreatmentOption] = []
    rationale: str


class BillingAuditRequest(BaseModel):
    patient_id: UUID
    treatment_id: UUID | None = None


class UnbilledItemSuggestion(BaseModel):
    item_type: str
    name: str
    code: str
    estimated_amount: float
    source: str


class BillingAuditResponse(BaseModel):
    has_unbilled_items: bool
    suggestions: list[UnbilledItemSuggestion] = []
    total_unbilled_estimate: float = 0.0


class SchedulingRecommendationRequest(BaseModel):
    patient_id: UUID
    procedure_name: str
    urgency: str | None = "NORMAL"


class SchedulingSlotRecommendation(BaseModel):
    recommended_duration_minutes: int
    dentist_id: UUID | None = None
    dentist_name: str | None = None
    suggested_dates: list[str] = []
    reason: str


class InventoryForecastItem(BaseModel):
    item_name: str
    category: str
    current_stock: float
    predicted_burn_rate_weekly: float
    projected_depletion_date: str
    recommended_reorder_qty: float
    urgency: str


class InventoryForecastResponse(BaseModel):
    forecasts: list[InventoryForecastItem] = []
    generated_at: str


class AIAnalyticsInsightsResponse(BaseModel):
    executive_summary: str
    revenue_insights: str
    chair_utilization_insights: str
    patient_retention_insights: str
    key_recommendations: list[str] = []


class AISearchRequest(BaseModel):
    query: str


class AISearchResultItem(BaseModel):
    entity_type: str
    id: str
    title: str
    subtitle: str
    detail: str
    link: str


class AISearchResponse(BaseModel):
    parsed_intent: str
    total_count: int
    results: list[AISearchResultItem] = []


class AIRecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    dentist_id: UUID
    recommendation_type: str
    status: str
    input_context_json: dict[str, Any]
    generated_output_json: dict[str, Any]
    reviewed_at: datetime | None = None
    clinician_feedback: str | None = None
    final_content: str | None = None
    created_at: datetime


class AIRecommendationReview(BaseModel):
    status: AIRecommendationStatus
    clinician_feedback: str | None = None
    final_content: str | None = None


class AIAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    user_id: UUID | None = None
    patient_id: UUID | None = None
    task_type: str
    provider_type: str
    model_name: str
    tokens_prompt: int
    tokens_completion: int
    latency_ms: int
    anonymized_prompt_summary: str | None = None
    response_summary: str | None = None
    safety_flags: list[str] = []
    request_id: str
    created_at: datetime
