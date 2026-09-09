"""Create insurance providers, plans, policies, coverage rules, preauthorizations, claims, claim items, and reconciliations tables.

Revision ID: 20260908_0012
Revises: 20260908_0011
Create Date: 2026-09-08 23:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0012"
down_revision = "20260908_0011"
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid()),
        sa.Column("updated_by", sa.Uuid()),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    ]


def upgrade() -> None:
    # 1. insurance_providers
    op.create_table(
        "insurance_providers",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_name", sa.String(150), nullable=False),
        sa.Column("provider_code", sa.String(60), nullable=False),
        sa.Column("contact_person", sa.String(120), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("payer_id", sa.String(60), nullable=True),
        sa.Column("tpa_name", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_insurance_providers_clinic", "insurance_providers", ["clinic_id"])
    op.create_index("ix_insurance_providers_code", "insurance_providers", ["provider_code"])

    # 2. insurance_plans
    op.create_table(
        "insurance_plans",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_name", sa.String(150), nullable=False),
        sa.Column("plan_code", sa.String(60), nullable=False),
        sa.Column("coverage_percentage", sa.Numeric(5, 2), server_default="80.00", nullable=False),
        sa.Column("annual_limit", sa.Numeric(12, 2), server_default="50000.00", nullable=False),
        sa.Column("lifetime_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("deductible", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("copayment_percentage", sa.Numeric(5, 2), server_default="20.00", nullable=False),
        sa.Column("copayment_fixed", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("maximum_claim_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("waiting_period_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("requires_preauth", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("coverage_rules_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_insurance_plans_clinic", "insurance_plans", ["clinic_id"])
    op.create_index("ix_insurance_plans_provider", "insurance_plans", ["provider_id"])

    # 3. patient_insurance_policies
    op.create_table(
        "patient_insurance_policies",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Uuid(), sa.ForeignKey("insurance_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_number", sa.String(100), nullable=False),
        sa.Column("member_id", sa.String(100), nullable=False),
        sa.Column("card_number", sa.String(100), nullable=True),
        sa.Column("group_number", sa.String(100), nullable=True),
        sa.Column("relationship", sa.String(40), server_default="SELF", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(40), server_default="ACTIVE", nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("remaining_annual_benefit", sa.Numeric(12, 2), nullable=True),
        sa.Column("policy_documents_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_patient_insurance_policies_clinic", "patient_insurance_policies", ["clinic_id"])
    op.create_index("ix_patient_insurance_policies_patient", "patient_insurance_policies", ["patient_id"])
    op.create_index("ix_patient_insurance_policies_number", "patient_insurance_policies", ["policy_number"])

    # 4. insurance_coverage_rules
    op.create_table(
        "insurance_coverage_rules",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Uuid(), sa.ForeignKey("insurance_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("procedure_code", sa.String(60), nullable=True),
        sa.Column("procedure_category", sa.String(60), nullable=True),
        sa.Column("coverage_type", sa.String(40), server_default="COVERED", nullable=False),
        sa.Column("coverage_percentage", sa.Numeric(5, 2), server_default="80.00", nullable=False),
        sa.Column("requires_preauth", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("waiting_period_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_payable_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_insurance_coverage_rules_plan", "insurance_coverage_rules", ["plan_id"])

    # 5. insurance_preauthorizations
    op.create_table(
        "insurance_preauthorizations",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Uuid(), sa.ForeignKey("patient_insurance_policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preauth_number", sa.String(60), nullable=False),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("requested_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("diagnoses_json", sa.JSON(), nullable=True),
        sa.Column("procedures_json", sa.JSON(), nullable=True),
        sa.Column("clinical_justification", sa.Text(), nullable=True),
        sa.Column("denial_reason", sa.Text(), nullable=True),
        sa.Column("attachments_json", sa.JSON(), nullable=True),
        sa.Column("advisory_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_insurance_preauthorizations_clinic", "insurance_preauthorizations", ["clinic_id"])
    op.create_index("ix_insurance_preauthorizations_patient", "insurance_preauthorizations", ["patient_id"])
    op.create_index("ix_insurance_preauthorizations_status", "insurance_preauthorizations", ["status"])

    # 6. insurance_claims
    op.create_table(
        "insurance_claims",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Uuid(), sa.ForeignKey("patient_insurance_policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("preauth_id", sa.Uuid(), sa.ForeignKey("insurance_preauthorizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_number", sa.String(60), nullable=False),
        sa.Column("batch_number", sa.String(60), nullable=True),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("total_claimed_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("approved_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("patient_copay_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("deductible_applied", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("disallowed_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("denial_reason", sa.Text(), nullable=True),
        sa.Column("denial_code", sa.String(60), nullable=True),
        sa.Column("tpa_reference_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("audit_trail_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_insurance_claims_clinic", "insurance_claims", ["clinic_id"])
    op.create_index("ix_insurance_claims_patient", "insurance_claims", ["patient_id"])
    op.create_index("ix_insurance_claims_status", "insurance_claims", ["status"])
    op.create_index("ix_insurance_claims_number", "insurance_claims", ["claim_number"])

    # 7. insurance_claim_items
    op.create_table(
        "insurance_claim_items",
        *audit_columns(),
        sa.Column("claim_id", sa.Uuid(), sa.ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_procedure_id", sa.Uuid(), nullable=True),
        sa.Column("procedure_code", sa.String(60), nullable=False),
        sa.Column("procedure_name", sa.String(255), nullable=False),
        sa.Column("tooth_number", sa.String(20), nullable=True),
        sa.Column("surface", sa.String(20), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_cost", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("covered_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("patient_responsibility", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("insurance_responsibility", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("status", sa.String(40), server_default="PENDING", nullable=False),
        sa.Column("denial_reason", sa.String(255), nullable=True),
    )
    op.create_index("ix_insurance_claim_items_claim", "insurance_claim_items", ["claim_id"])

    # 8. insurance_payment_reconciliations
    op.create_table(
        "insurance_payment_reconciliations",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_id", sa.Uuid(), sa.ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reconciliation_reference", sa.String(100), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("total_claim_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("insurance_settled_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("patient_copay_due", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("adjustment_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("settlement_type", sa.String(40), server_default="FULL", nullable=False),
        sa.Column("bank_reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), server_default="RECONCILED", nullable=False),
    )
    op.create_index("ix_insurance_reconciliations_clinic", "insurance_payment_reconciliations", ["clinic_id"])
    op.create_index("ix_insurance_reconciliations_claim", "insurance_payment_reconciliations", ["claim_id"])


def downgrade() -> None:
    op.drop_table("insurance_payment_reconciliations")
    op.drop_table("insurance_claim_items")
    op.drop_table("insurance_claims")
    op.drop_table("insurance_preauthorizations")
    op.drop_table("insurance_coverage_rules")
    op.drop_table("patient_insurance_policies")
    op.drop_table("insurance_plans")
    op.drop_table("insurance_providers")
