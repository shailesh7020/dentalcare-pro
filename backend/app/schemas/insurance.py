from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.insurance import (
    ClaimItemStatus,
    ClaimStatus,
    CoverageType,
    PolicyStatus,
    PreAuthStatus,
    ReconciliationStatus,
    SettlementType,
)

# ---------------------------------------------------------------------------
# 1. Insurance Providers
# ---------------------------------------------------------------------------

class InsuranceProviderBase(BaseModel):
    provider_name: str = Field(..., max_length=150)
    provider_code: str = Field(..., max_length=60)
    contact_person: str | None = Field(None, max_length=120)
    address: str | None = None
    email: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=40)
    website: str | None = Field(None, max_length=255)
    payer_id: str | None = Field(None, max_length=60)
    tpa_name: str | None = Field(None, max_length=120)
    is_active: bool = True
    notes: str | None = None


class InsuranceProviderCreate(InsuranceProviderBase):
    pass


class InsuranceProviderUpdate(BaseModel):
    provider_name: str | None = None
    provider_code: str | None = None
    contact_person: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    payer_id: str | None = None
    tpa_name: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class InsuranceProviderRead(InsuranceProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 2. Insurance Plans
# ---------------------------------------------------------------------------

class InsurancePlanBase(BaseModel):
    plan_name: str = Field(..., max_length=150)
    plan_code: str = Field(..., max_length=60)
    coverage_percentage: float = Field(80.00, ge=0.0, le=100.0)
    annual_limit: float = Field(50000.00, ge=0.0)
    lifetime_limit: float | None = None
    deductible: float = Field(0.00, ge=0.0)
    copayment_percentage: float = Field(20.00, ge=0.0, le=100.0)
    copayment_fixed: float = Field(0.00, ge=0.0)
    maximum_claim_amount: float | None = None
    waiting_period_days: int = Field(0, ge=0)
    requires_preauth: bool = False
    coverage_rules_json: dict | None = None
    is_active: bool = True
    notes: str | None = None

    @field_validator("deductible", "copayment_fixed", mode="before")
    @classmethod
    def _default_zero_float(cls, v: float | None) -> float:
        return 0.0 if v is None else float(v)

    @field_validator("copayment_percentage", mode="before")
    @classmethod
    def _default_copay_pct(cls, v: float | None) -> float:
        return 20.0 if v is None else float(v)

    @field_validator("waiting_period_days", mode="before")
    @classmethod
    def _default_waiting_days(cls, v: int | None) -> int:
        return 0 if v is None else int(v)

    @field_validator("requires_preauth", mode="before")
    @classmethod
    def _default_preauth(cls, v: bool | None) -> bool:
        return False if v is None else bool(v)

    @field_validator("is_active", mode="before")
    @classmethod
    def _default_active(cls, v: bool | None) -> bool:
        return True if v is None else bool(v)


class InsurancePlanCreate(InsurancePlanBase):
    provider_id: UUID


class InsurancePlanUpdate(BaseModel):
    plan_name: str | None = None
    plan_code: str | None = None
    coverage_percentage: float | None = None
    annual_limit: float | None = None
    lifetime_limit: float | None = None
    deductible: float | None = None
    copayment_percentage: float | None = None
    copayment_fixed: float | None = None
    maximum_claim_amount: float | None = None
    waiting_period_days: int | None = None
    requires_preauth: bool | None = None
    coverage_rules_json: dict | None = None
    is_active: bool | None = None
    notes: str | None = None


class InsurancePlanRead(InsurancePlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    provider_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _default_datetime(cls, v: datetime | None) -> datetime:
        return datetime.now(UTC) if v is None else v


class InsuranceProviderDetail(InsuranceProviderRead):
    plans: list[InsurancePlanRead] = []


# ---------------------------------------------------------------------------
# 3. Patient Insurance Policies
# ---------------------------------------------------------------------------

class PatientInsurancePolicyBase(BaseModel):
    policy_number: str = Field(..., max_length=100)
    member_id: str = Field(..., max_length=100)
    card_number: str | None = None
    group_number: str | None = None
    relationship: str = "SELF"
    is_primary: bool = True
    effective_date: date
    expiry_date: date
    status: PolicyStatus = PolicyStatus.ACTIVE
    remaining_annual_benefit: float | None = None
    policy_documents_json: list | None = None
    notes: str | None = None


class PatientInsurancePolicyCreate(PatientInsurancePolicyBase):
    patient_id: UUID
    provider_id: UUID
    plan_id: UUID | None = None


class PatientInsurancePolicyUpdate(BaseModel):
    policy_number: str | None = None
    member_id: str | None = None
    card_number: str | None = None
    group_number: str | None = None
    relationship: str | None = None
    is_primary: bool | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    status: PolicyStatus | None = None
    remaining_annual_benefit: float | None = None
    policy_documents_json: list | None = None
    notes: str | None = None


class PatientInsurancePolicyRead(PatientInsurancePolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    provider_id: UUID
    plan_id: UUID | None = None
    verified_at: datetime | None = None
    verified_by: UUID | None = None
    provider_name: str | None = None
    plan_name: str | None = None
    created_at: datetime
    updated_at: datetime


class PolicyVerificationRequest(BaseModel):
    is_verified: bool = True
    verified_by: UUID | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# 4. Coverage Rules
# ---------------------------------------------------------------------------

class InsuranceCoverageRuleBase(BaseModel):
    procedure_code: str | None = None
    procedure_category: str | None = None
    coverage_type: CoverageType = CoverageType.COVERED
    coverage_percentage: float = Field(80.00, ge=0.0, le=100.0)
    requires_preauth: bool = False
    waiting_period_days: int = 0
    max_payable_amount: float | None = None
    notes: str | None = None

    @field_validator("requires_preauth", mode="before")
    @classmethod
    def _default_rule_preauth(cls, v: bool | None) -> bool:
        return False if v is None else bool(v)

    @field_validator("waiting_period_days", mode="before")
    @classmethod
    def _default_rule_waiting(cls, v: int | None) -> int:
        return 0 if v is None else int(v)


class InsuranceCoverageRuleCreate(InsuranceCoverageRuleBase):
    plan_id: UUID


class InsuranceCoverageRuleRead(InsuranceCoverageRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    plan_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("created_at", mode="before")
    @classmethod
    def _default_rule_datetime(cls, v: datetime | None) -> datetime:
        return datetime.now(UTC) if v is None else v


# ---------------------------------------------------------------------------
# 5. Pre-Authorizations
# ---------------------------------------------------------------------------

class PreAuthCreate(BaseModel):
    patient_id: UUID
    policy_id: UUID
    treatment_id: UUID | None = None
    requested_amount: float = Field(..., ge=0.0)
    diagnoses_json: list | None = None
    procedures_json: list | None = None
    clinical_justification: str | None = None
    attachments_json: list | None = None
    advisory_notes: str | None = None


class PreAuthStatusUpdate(BaseModel):
    status: PreAuthStatus
    approved_amount: float | None = None
    denial_reason: str | None = None
    approval_date: date | None = None
    expiry_date: date | None = None
    advisory_notes: str | None = None


class PreAuthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    policy_id: UUID
    treatment_id: UUID | None = None
    preauth_number: str
    status: PreAuthStatus
    requested_amount: float
    approved_amount: float
    submission_date: date | None = None
    approval_date: date | None = None
    expiry_date: date | None = None
    diagnoses_json: list | None = None
    procedures_json: list | None = None
    clinical_justification: str | None = None
    denial_reason: str | None = None
    attachments_json: list | None = None
    advisory_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("approved_amount", mode="before")
    @classmethod
    def _default_pa_approved(cls, v: float | None) -> float:
        return 0.0 if v is None else float(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _default_pa_datetime(cls, v: datetime | None) -> datetime:
        return datetime.now(UTC) if v is None else v


# ---------------------------------------------------------------------------
# 6. Claims & Claim Items
# ---------------------------------------------------------------------------

class ClaimItemCreate(BaseModel):
    procedure_code: str = Field(..., max_length=60)
    procedure_name: str = Field(..., max_length=255)
    tooth_number: str | None = None
    surface: str | None = None
    quantity: int = Field(1, ge=1)
    unit_cost: float = Field(..., ge=0.0)
    total_cost: float = Field(..., ge=0.0)
    covered_amount: float = Field(0.00, ge=0.0)
    patient_responsibility: float = Field(0.00, ge=0.0)
    insurance_responsibility: float = Field(0.00, ge=0.0)
    treatment_procedure_id: UUID | None = None


class ClaimItemRead(ClaimItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    status: ClaimItemStatus = ClaimItemStatus.PENDING
    denial_reason: str | None = None
    created_at: datetime


class ClaimCreate(BaseModel):
    patient_id: UUID
    policy_id: UUID
    preauth_id: UUID | None = None
    treatment_id: UUID | None = None
    invoice_id: UUID | None = None
    total_claimed_amount: float = Field(..., ge=0.0)
    items: list[ClaimItemCreate] = []
    notes: str | None = None


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    approved_amount: float | None = None
    patient_copay_amount: float | None = None
    deductible_applied: float | None = None
    disallowed_amount: float | None = None
    paid_amount: float | None = None
    denial_reason: str | None = None
    denial_code: str | None = None
    tpa_reference_number: str | None = None
    notes: str | None = None


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    policy_id: UUID
    preauth_id: UUID | None = None
    treatment_id: UUID | None = None
    invoice_id: UUID | None = None
    claim_number: str
    batch_number: str | None = None
    status: ClaimStatus
    submission_date: date | None = None
    approval_date: date | None = None
    payment_date: date | None = None
    total_claimed_amount: float
    approved_amount: float
    patient_copay_amount: float
    deductible_applied: float
    disallowed_amount: float
    paid_amount: float
    denial_reason: str | None = None
    denial_code: str | None = None
    tpa_reference_number: str | None = None
    notes: str | None = None
    patient_name: str | None = None
    provider_name: str | None = None
    policy_number: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "approved_amount",
        "patient_copay_amount",
        "deductible_applied",
        "disallowed_amount",
        "paid_amount",
        mode="before",
    )
    @classmethod
    def _default_claim_amounts(cls, v: float | None) -> float:
        return 0.0 if v is None else float(v)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _default_claim_datetime(cls, v: datetime | None) -> datetime:
        return datetime.now(UTC) if v is None else v


class ClaimDetail(ClaimRead):
    items: list[ClaimItemRead] = []
    audit_trail_json: list | None = None


# ---------------------------------------------------------------------------
# 7. Payment Reconciliation
# ---------------------------------------------------------------------------

class PaymentReconciliationCreate(BaseModel):
    claim_id: UUID
    invoice_id: UUID | None = None
    reconciliation_reference: str = Field(..., max_length=100)
    payment_date: date
    insurance_settled_amount: float = Field(..., ge=0.0)
    patient_copay_due: float = Field(0.00, ge=0.0)
    adjustment_amount: float = Field(0.00, ge=0.0)
    settlement_type: SettlementType = SettlementType.FULL
    bank_reference: str | None = None
    notes: str | None = None


class PaymentReconciliationRead(PaymentReconciliationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    total_claim_amount: float
    status: ReconciliationStatus
    created_at: datetime


# ---------------------------------------------------------------------------
# 8. Dashboard & Reports
# ---------------------------------------------------------------------------

class InsuranceDashboardStats(BaseModel):
    pending_claims_count: int
    pending_claims_amount: float
    approved_claims_count: int
    approved_claims_amount: float
    rejected_claims_count: int
    rejected_claims_amount: float
    paid_claims_count: int
    total_insurance_revenue: float
    average_turnaround_days: float
    outstanding_insurance_balance: float


class ClaimsReportItem(BaseModel):
    claim_id: str
    claim_number: str
    patient_name: str
    provider_name: str
    submission_date: str | None
    status: str
    claimed_amount: float
    approved_amount: float
    paid_amount: float
    patient_copay: float


class ClaimsReportResponse(BaseModel):
    total_count: int
    total_claimed: float
    total_approved: float
    total_paid: float
    claims: list[ClaimsReportItem]


class ProviderPerformanceItem(BaseModel):
    provider_id: str
    provider_name: str
    provider_code: str
    total_claims: int
    approved_claims: int
    rejected_claims: int
    approval_rate_pct: float
    total_paid: float
    avg_turnaround_days: float


class ProviderPerformanceResponse(BaseModel):
    providers: list[ProviderPerformanceItem]


# ---------------------------------------------------------------------------
# 9. AI Insurance Assistant
# ---------------------------------------------------------------------------

class ClaimCompletenessAuditResponse(BaseModel):
    claim_id: str
    completeness_score: int
    is_ready_for_submission: bool
    missing_documents: list[str]
    warnings: list[str]
    recommendations: list[str]
    disclaimer: str


class CodingSuggestionItem(BaseModel):
    procedure_name: str
    suggested_cdt_code: str
    description: str
    standard_category: str
    typical_coverage_pct: float
    rationale: str


class CodingSuggestionResponse(BaseModel):
    suggestions: list[CodingSuggestionItem]
    disclaimer: str


class RejectionAnalysisResponse(BaseModel):
    claim_id: str
    denial_code: str | None
    denial_reason: str | None
    root_cause_analysis: str
    appeal_likelihood: str
    suggested_appeal_letter: str
    required_evidence: list[str]
    disclaimer: str
