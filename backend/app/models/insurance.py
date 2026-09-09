from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.billing import Invoice
    from app.models.identity import Clinic
    from app.models.patient import Patient
    from app.models.treatment import Treatment


class PolicyStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class CoverageType(StrEnum):
    COVERED = "COVERED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    EXCLUDED = "EXCLUDED"


class PreAuthStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ClaimStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    ADDITIONAL_INFO_REQUESTED = "ADDITIONAL_INFO_REQUESTED"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CLOSED = "CLOSED"


class ClaimItemStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISALLOWED = "DISALLOWED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"


class SettlementType(StrEnum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    DISALLOWED = "DISALLOWED"
    REVERSED = "REVERSED"


class ReconciliationStatus(StrEnum):
    PENDING = "PENDING"
    RECONCILED = "RECONCILED"
    DISPUTED = "DISPUTED"


class InsuranceProvider(Base, UUIDAuditMixin):
    __tablename__ = "insurance_providers"
    __table_args__ = (
        Index("ix_insurance_providers_clinic", "clinic_id"),
        Index("ix_insurance_providers_code", "provider_code"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider_code: Mapped[str] = mapped_column(String(60), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(40))
    website: Mapped[str | None] = mapped_column(String(255))
    payer_id: Mapped[str | None] = mapped_column(String(60))
    tpa_name: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped[Clinic] = orm_relationship("Clinic")
    plans: Mapped[list[InsurancePlan]] = orm_relationship(
        "InsurancePlan",
        back_populates="provider",
        cascade="all, delete-orphan",
    )
    policies: Mapped[list[PatientInsurancePolicy]] = orm_relationship(
        "PatientInsurancePolicy",
        back_populates="provider",
    )


class InsurancePlan(Base, UUIDAuditMixin):
    __tablename__ = "insurance_plans"
    __table_args__ = (
        Index("ix_insurance_plans_clinic", "clinic_id"),
        Index("ix_insurance_plans_provider", "provider_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False
    )
    plan_name: Mapped[str] = mapped_column(String(150), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(60), nullable=False)
    coverage_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=80.00, nullable=False)
    annual_limit: Mapped[float] = mapped_column(Numeric(12, 2), default=50000.00, nullable=False)
    lifetime_limit: Mapped[float | None] = mapped_column(Numeric(12, 2))
    deductible: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    copayment_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=20.00, nullable=False)
    copayment_fixed: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    maximum_claim_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    waiting_period_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_preauth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coverage_rules_json: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    provider: Mapped[InsuranceProvider] = orm_relationship("InsuranceProvider", back_populates="plans")
    coverage_rules: Mapped[list[InsuranceCoverageRule]] = orm_relationship(
        "InsuranceCoverageRule",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    policies: Mapped[list[PatientInsurancePolicy]] = orm_relationship(
        "PatientInsurancePolicy",
        back_populates="plan",
    )


class PatientInsurancePolicy(Base, UUIDAuditMixin):
    __tablename__ = "patient_insurance_policies"
    __table_args__ = (
        Index("ix_patient_insurance_policies_clinic", "clinic_id"),
        Index("ix_patient_insurance_policies_patient", "patient_id"),
        Index("ix_patient_insurance_policies_number", "policy_number"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("insurance_plans.id", ondelete="SET NULL")
    )
    policy_number: Mapped[str] = mapped_column(String(100), nullable=False)
    member_id: Mapped[str] = mapped_column(String(100), nullable=False)
    card_number: Mapped[str | None] = mapped_column(String(100))
    group_number: Mapped[str | None] = mapped_column(String(100))
    relationship: Mapped[str] = mapped_column(String(40), default="SELF", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="insurance_policy_status"),
        default=PolicyStatus.ACTIVE,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    remaining_annual_benefit: Mapped[float | None] = mapped_column(Numeric(12, 2))
    policy_documents_json: Mapped[list | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    patient: Mapped[Patient] = orm_relationship("Patient")
    provider: Mapped[InsuranceProvider] = orm_relationship("InsuranceProvider", back_populates="policies")
    plan: Mapped[InsurancePlan | None] = orm_relationship("InsurancePlan", back_populates="policies")
    claims: Mapped[list[InsuranceClaim]] = orm_relationship("InsuranceClaim", back_populates="policy")
    preauthorizations: Mapped[list[InsurancePreAuthorization]] = orm_relationship(
        "InsurancePreAuthorization",
        back_populates="policy",
    )


class InsuranceCoverageRule(Base, UUIDAuditMixin):
    __tablename__ = "insurance_coverage_rules"
    __table_args__ = (
        Index("ix_insurance_coverage_rules_plan", "plan_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_plans.id", ondelete="CASCADE"), nullable=False
    )
    procedure_code: Mapped[str | None] = mapped_column(String(60))
    procedure_category: Mapped[str | None] = mapped_column(String(60))
    coverage_type: Mapped[CoverageType] = mapped_column(
        Enum(CoverageType, name="insurance_coverage_type"),
        default=CoverageType.COVERED,
        nullable=False,
    )
    coverage_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=80.00, nullable=False)
    requires_preauth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    waiting_period_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_payable_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    plan: Mapped[InsurancePlan] = orm_relationship("InsurancePlan", back_populates="coverage_rules")


class InsurancePreAuthorization(Base, UUIDAuditMixin):
    __tablename__ = "insurance_preauthorizations"
    __table_args__ = (
        Index("ix_insurance_preauthorizations_clinic", "clinic_id"),
        Index("ix_insurance_preauthorizations_patient", "patient_id"),
        Index("ix_insurance_preauthorizations_status", "status"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient_insurance_policies.id", ondelete="CASCADE"), nullable=False
    )
    treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id", ondelete="SET NULL"))
    preauth_number: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[PreAuthStatus] = mapped_column(
        Enum(PreAuthStatus, name="insurance_preauth_status"),
        default=PreAuthStatus.DRAFT,
        nullable=False,
    )
    requested_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    approved_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    submission_date: Mapped[date | None] = mapped_column(Date)
    approval_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    diagnoses_json: Mapped[list | None] = mapped_column(JSON)
    procedures_json: Mapped[list | None] = mapped_column(JSON)
    clinical_justification: Mapped[str | None] = mapped_column(Text)
    denial_reason: Mapped[str | None] = mapped_column(Text)
    attachments_json: Mapped[list | None] = mapped_column(JSON)
    advisory_notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    patient: Mapped[Patient] = orm_relationship("Patient")
    policy: Mapped[PatientInsurancePolicy] = orm_relationship("PatientInsurancePolicy", back_populates="preauthorizations")
    treatment: Mapped[Treatment | None] = orm_relationship("Treatment")
    claims: Mapped[list[InsuranceClaim]] = orm_relationship("InsuranceClaim", back_populates="preauthorization")


class InsuranceClaim(Base, UUIDAuditMixin):
    __tablename__ = "insurance_claims"
    __table_args__ = (
        Index("ix_insurance_claims_clinic", "clinic_id"),
        Index("ix_insurance_claims_patient", "patient_id"),
        Index("ix_insurance_claims_status", "status"),
        Index("ix_insurance_claims_number", "claim_number"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient_insurance_policies.id", ondelete="CASCADE"), nullable=False
    )
    preauth_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("insurance_preauthorizations.id", ondelete="SET NULL")
    )
    treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id", ondelete="SET NULL"))
    invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    claim_number: Mapped[str] = mapped_column(String(60), nullable=False)
    batch_number: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="insurance_claim_status"),
        default=ClaimStatus.DRAFT,
        nullable=False,
    )
    submission_date: Mapped[date | None] = mapped_column(Date)
    approval_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    total_claimed_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    approved_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    patient_copay_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    deductible_applied: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    disallowed_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(Text)
    denial_code: Mapped[str | None] = mapped_column(String(60))
    tpa_reference_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    audit_trail_json: Mapped[list | None] = mapped_column(JSON)

    # Relationships
    patient: Mapped[Patient] = orm_relationship("Patient")
    policy: Mapped[PatientInsurancePolicy] = orm_relationship("PatientInsurancePolicy", back_populates="claims")
    preauthorization: Mapped[InsurancePreAuthorization | None] = orm_relationship(
        "InsurancePreAuthorization",
        back_populates="claims",
    )
    treatment: Mapped[Treatment | None] = orm_relationship("Treatment")
    invoice: Mapped[Invoice | None] = orm_relationship("Invoice")
    items: Mapped[list[InsuranceClaimItem]] = orm_relationship(
        "InsuranceClaimItem",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    reconciliations: Mapped[list[InsurancePaymentReconciliation]] = orm_relationship(
        "InsurancePaymentReconciliation",
        back_populates="claim",
    )


class InsuranceClaimItem(Base, UUIDAuditMixin):
    __tablename__ = "insurance_claim_items"
    __table_args__ = (
        Index("ix_insurance_claim_items_claim", "claim_id"),
    )

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False
    )
    treatment_procedure_id: Mapped[UUID | None] = mapped_column()
    procedure_code: Mapped[str] = mapped_column(String(60), nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tooth_number: Mapped[str | None] = mapped_column(String(20))
    surface: Mapped[str | None] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    covered_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    patient_responsibility: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    insurance_responsibility: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    status: Mapped[ClaimItemStatus] = mapped_column(
        Enum(ClaimItemStatus, name="insurance_claim_item_status"),
        default=ClaimItemStatus.PENDING,
        nullable=False,
    )
    denial_reason: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    claim: Mapped[InsuranceClaim] = orm_relationship("InsuranceClaim", back_populates="items")


class InsurancePaymentReconciliation(Base, UUIDAuditMixin):
    __tablename__ = "insurance_payment_reconciliations"
    __table_args__ = (
        Index("ix_insurance_reconciliations_clinic", "clinic_id"),
        Index("ix_insurance_reconciliations_claim", "claim_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    reconciliation_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_claim_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    insurance_settled_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    patient_copay_due: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    adjustment_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    settlement_type: Mapped[SettlementType] = mapped_column(
        Enum(SettlementType, name="insurance_settlement_type"),
        default=SettlementType.FULL,
        nullable=False,
    )
    bank_reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(ReconciliationStatus, name="insurance_reconciliation_status"),
        default=ReconciliationStatus.RECONCILED,
        nullable=False,
    )

    # Relationships
    claim: Mapped[InsuranceClaim] = orm_relationship("InsuranceClaim", back_populates="reconciliations")
    invoice: Mapped[Invoice | None] = orm_relationship("Invoice")
