from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.billing import Invoice
from app.models.insurance import (
    ClaimStatus,
    CoverageType,
    InsuranceClaim,
    InsuranceCoverageRule,
    InsurancePaymentReconciliation,
    InsurancePlan,
    InsurancePreAuthorization,
    InsuranceProvider,
    PatientInsurancePolicy,
    PolicyStatus,
    PreAuthStatus,
    ReconciliationStatus,
    SettlementType,
)
from app.repositories.insurance_repository import InsuranceRepository
from app.schemas.insurance import (
    ClaimCreate,
    ClaimItemCreate,
    ClaimStatusUpdate,
    InsuranceCoverageRuleCreate,
    InsurancePlanCreate,
    InsurancePlanUpdate,
    InsuranceProviderCreate,
    InsuranceProviderUpdate,
    PatientInsurancePolicyCreate,
    PaymentReconciliationCreate,
    PreAuthCreate,
    PreAuthStatusUpdate,
)


class ScalarResult:
    def __init__(self, values):
        self._values = list(values) if values is not None else []

    def all(self):
        return self._values

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None

    def one(self):
        if not self._values:
            return 0, 0.0
        return self._values[0]


class FakeAsyncDb:
    def __init__(self, items=None):
        self.items = list(items) if items else []
        self.added = []

    def add(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = uuid4()
        if not hasattr(item, "created_at") or item.created_at is None:
            item.created_at = datetime.now(UTC)
        if not hasattr(item, "updated_at") or item.updated_at is None:
            item.updated_at = datetime.now(UTC)
        if not hasattr(item, "deleted_at"):
            item.deleted_at = None
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, item):
        pass

    async def execute(self, query):
        stmt_str = str(query)

        if "insurance_providers" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsuranceProvider) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_plans" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePlan) and x.deleted_at is None]
            return ScalarResult(res)

        if "patient_insurance_policies" in stmt_str:
            res = [x for x in self.items if isinstance(x, PatientInsurancePolicy) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_coverage_rules" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsuranceCoverageRule) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_preauthorizations" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePreAuthorization) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_claims" in stmt_str:
            if "count" in stmt_str.lower():
                claims = [x for x in self.items if isinstance(x, InsuranceClaim) and x.deleted_at is None]
                count = len(claims)
                amt = sum(float(x.total_claimed_amount or 0.0) for x in claims)
                return ScalarResult([(count, amt)])
            res = [x for x in self.items if isinstance(x, InsuranceClaim) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_payment_reconciliations" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePaymentReconciliation) and x.deleted_at is None]
            return ScalarResult(res)

        if "invoices" in stmt_str:
            res = [x for x in self.items if isinstance(x, Invoice) and x.deleted_at is None]
            return ScalarResult(res)

        return ScalarResult(self.items)


@pytest.mark.asyncio
async def test_insurance_provider_crud():
    clinic_id = uuid4()
    db = FakeAsyncDb()
    repo = InsuranceRepository(db)

    # 1. Create provider
    create_dto = InsuranceProviderCreate(
        provider_name="Delta Dental Pro",
        provider_code="DELTA",
        contact_person="Jane Doe",
        email="claims@deltadental.com",
        phone="+1 800 555 1234",
        is_active=True,
    )
    p = await repo.create_provider(clinic_id, create_dto)
    assert p.provider_name == "Delta Dental Pro"
    assert p.provider_code == "DELTA"
    assert p.is_active is True

    # 2. List providers
    providers = await repo.list_providers(clinic_id)
    assert len(providers) >= 1

    # 3. Update provider
    up_dto = InsuranceProviderUpdate(contact_person="John Smith", notes="Preferred payer contract")
    up = await repo.update_provider(clinic_id, p.id, up_dto)
    assert up is not None
    assert up.contact_person == "John Smith"


@pytest.mark.asyncio
async def test_insurance_plan_and_coverage_rules():
    clinic_id = uuid4()
    provider_id = uuid4()
    db = FakeAsyncDb()
    repo = InsuranceRepository(db)

    # 1. Create plan
    plan_dto = InsurancePlanCreate(
        provider_id=provider_id,
        plan_name="Comprehensive Gold Dental PPO",
        plan_code="GOLD-PPO",
        coverage_percentage=80.0,
        annual_limit=25000.0,
        deductible=500.0,
        copayment_percentage=20.0,
        waiting_period_days=30,
        requires_preauth=True,
    )
    plan = await repo.create_plan(clinic_id, plan_dto)
    assert plan.plan_name == "Comprehensive Gold Dental PPO"
    assert plan.coverage_percentage == 80.0
    assert plan.annual_limit == 25000.0

    # 2. Update plan
    up_plan = await repo.update_plan(clinic_id, plan.id, InsurancePlanUpdate(annual_limit=30000.0))
    assert up_plan is not None
    assert up_plan.annual_limit == 30000.0

    # 3. Create coverage rule
    rule_dto = InsuranceCoverageRuleCreate(
        plan_id=plan.id,
        procedure_code="D3330",
        procedure_category="Endodontics",
        coverage_type=CoverageType.COVERED,
        coverage_percentage=80.0,
        requires_preauth=True,
    )
    rule = await repo.create_coverage_rule(clinic_id, rule_dto)
    assert rule.procedure_code == "D3330"
    assert rule.coverage_percentage == 80.0


@pytest.mark.asyncio
async def test_patient_insurance_policy_and_verification():
    clinic_id = uuid4()
    patient_id = uuid4()
    provider_id = uuid4()
    plan_id = uuid4()

    db = FakeAsyncDb()
    repo = InsuranceRepository(db)

    # 1. Create policy
    policy_dto = PatientInsurancePolicyCreate(
        patient_id=patient_id,
        provider_id=provider_id,
        plan_id=plan_id,
        policy_number="POL-DELTA-9842",
        member_id="MEM-77491",
        relationship="SELF",
        is_primary=True,
        effective_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        status=PolicyStatus.PENDING_VERIFICATION,
    )
    policy = await repo.create_policy(clinic_id, policy_dto)
    assert policy.policy_number == "POL-DELTA-9842"
    assert policy.status == PolicyStatus.PENDING_VERIFICATION

    # 2. Verify policy
    verified = await repo.verify_policy(clinic_id, policy.id, verified_by=uuid4(), notes="Verified active via portal")
    assert verified is not None
    assert verified.status == PolicyStatus.ACTIVE
    assert verified.verified_at is not None


@pytest.mark.asyncio
async def test_preauth_and_claim_lifecycle():
    clinic_id = uuid4()
    patient_id = uuid4()
    policy_id = uuid4()

    db = FakeAsyncDb()
    repo = InsuranceRepository(db)

    # 1. Pre-authorization
    pa_dto = PreAuthCreate(
        patient_id=patient_id,
        policy_id=policy_id,
        requested_amount=15000.0,
        procedures_json=[{"code": "D3330", "tooth": "46"}],
        clinical_justification="Irreversible pulpitis on tooth #46",
    )
    pa = await repo.create_preauth(clinic_id, pa_dto)
    assert pa.preauth_number.startswith("PA-")
    assert pa.status == PreAuthStatus.DRAFT

    pa_updated = await repo.update_preauth_status(
        clinic_id, pa.id, PreAuthStatusUpdate(status=PreAuthStatus.APPROVED, approved_amount=12000.0)
    )
    assert pa_updated is not None
    assert pa_updated.status == PreAuthStatus.APPROVED
    assert pa_updated.approved_amount == 12000.0

    # 2. Claim Creation with Items
    claim_dto = ClaimCreate(
        patient_id=patient_id,
        policy_id=policy_id,
        preauth_id=pa.id,
        total_claimed_amount=15000.0,
        items=[
            ClaimItemCreate(
                procedure_code="D3330",
                procedure_name="Molar Root Canal",
                tooth_number="46",
                quantity=1,
                unit_cost=15000.0,
                total_cost=15000.0,
                covered_amount=12000.0,
                patient_responsibility=3000.0,
                insurance_responsibility=12000.0,
            )
        ],
        notes="Claim submission for completed RCT",
    )
    claim = await repo.create_claim(clinic_id, claim_dto)
    assert claim.claim_number.startswith("CLM-")
    assert claim.status == ClaimStatus.DRAFT
    assert len(claim.items) == 1
    assert claim.items[0].procedure_code == "D3330"

    # 3. Update claim to approved
    c_updated = await repo.update_claim_status(
        clinic_id, claim.id, ClaimStatusUpdate(status=ClaimStatus.APPROVED, approved_amount=12000.0, patient_copay_amount=3000.0)
    )
    assert c_updated is not None
    assert c_updated.status == ClaimStatus.APPROVED
    assert c_updated.approved_amount == 12000.0


@pytest.mark.asyncio
async def test_reconciliation_and_invoice_update():
    clinic_id = uuid4()
    patient_id = uuid4()
    invoice_id = uuid4()
    claim_id = uuid4()

    # Seed invoice
    invoice = Invoice(
        id=invoice_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=uuid4(),
        invoice_number="INV-2026-0091",
        date=datetime.now(UTC).date(),
        subtotal=15000.0,
        discount_amount=0.0,
        tax_amount=0.0,
        grand_total=15000.0,
        amount_paid=0.0,
        balance_due=15000.0,
        created_by=uuid4(),
        updated_by=uuid4(),
    )
    # Seed claim
    claim = InsuranceClaim(
        id=claim_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        policy_id=uuid4(),
        invoice_id=invoice_id,
        claim_number="CLM-2026-0091",
        status=ClaimStatus.APPROVED,
        total_claimed_amount=15000.0,
        approved_amount=12000.0,
        paid_amount=0.0,
    )

    db = FakeAsyncDb([invoice, claim])
    repo = InsuranceRepository(db)

    rec_dto = PaymentReconciliationCreate(
        claim_id=claim_id,
        invoice_id=invoice_id,
        reconciliation_reference="EFT-REMIT-9941",
        payment_date=datetime.now(UTC).date(),
        insurance_settled_amount=12000.0,
        patient_copay_due=3000.0,
        adjustment_amount=0.0,
        settlement_type=SettlementType.FULL,
        bank_reference="HDFC-NEFT-884910",
        notes="Remittance settled via clearinghouse",
    )
    rec = await repo.create_reconciliation(clinic_id, rec_dto)
    assert rec.reconciliation_reference == "EFT-REMIT-9941"
    assert rec.status == ReconciliationStatus.RECONCILED

    # Check that claim updated to PAID
    assert claim.status == ClaimStatus.PAID
    assert claim.paid_amount == 12000.0

    # Check that invoice amount_paid and balance_due updated
    assert invoice.amount_paid == 12000.0
    assert invoice.balance_due == 3000.0
