from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.api.v1 import insurance as ins_api
from app.models.identity import Role, User
from app.models.insurance import (
    ClaimStatus,
    InsuranceClaim,
    InsurancePlan,
    InsurancePreAuthorization,
    InsuranceProvider,
    PatientInsurancePolicy,
    PolicyStatus,
    PreAuthStatus,
    SettlementType,
)
from app.schemas.insurance import (
    ClaimCreate,
    ClaimItemCreate,
    ClaimStatusUpdate,
    InsurancePlanCreate,
    InsuranceProviderCreate,
    PatientInsurancePolicyCreate,
    PaymentReconciliationCreate,
    PolicyVerificationRequest,
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

        if "insurance_preauthorizations" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePreAuthorization) and x.deleted_at is None]
            return ScalarResult(res)

        if "insurance_claims" in stmt_str:
            if "count" in stmt_str.lower():
                claims = [x for x in self.items if isinstance(x, InsuranceClaim) and x.deleted_at is None]
                return ScalarResult([(len(claims), sum(float(c.total_claimed_amount or 0.0) for c in claims))])
            res = [x for x in self.items if isinstance(x, InsuranceClaim) and x.deleted_at is None]
            return ScalarResult(res)

        return ScalarResult(self.items)


def make_user(role=Role.CLINIC_ADMIN, clinic_id=None):
    cid = clinic_id or uuid4()
    return User(
        id=uuid4(),
        clinic_id=cid,
        email="admin@brightsmiledental.com",
        first_name="Admin",
        last_name="User",
        role=role,
    )


@pytest.mark.asyncio
async def test_api_dashboard():
    user = make_user()
    db = FakeAsyncDb()
    stats = await ins_api.get_insurance_dashboard(current_user=user, db=db, clinic_id=None)
    assert stats is not None
    assert stats.pending_claims_count >= 0
    assert stats.average_turnaround_days > 0


@pytest.mark.asyncio
async def test_api_providers_and_plans():
    user = make_user()
    db = FakeAsyncDb()

    # Create Provider
    prov_payload = InsuranceProviderCreate(
        provider_name="MetLife Dental",
        provider_code="METLIFE",
        contact_person="Alice B.",
        email="provider@metlife.com",
        phone="+1 800 638 5433",
        is_active=True,
    )
    provider = await ins_api.create_provider(payload=prov_payload, current_user=user, db=db, clinic_id=None)
    assert provider.provider_name == "MetLife Dental"

    # List Providers
    prov_list = await ins_api.list_providers(current_user=user, db=db, clinic_id=None)
    assert len(prov_list) >= 1

    # Create Plan
    plan_payload = InsurancePlanCreate(
        provider_id=provider.id,
        plan_name="MetLife Preferred PPO",
        plan_code="MET-PPO",
        coverage_percentage=80.0,
        annual_limit=30000.0,
    )
    plan = await ins_api.create_plan(payload=plan_payload, current_user=user, db=db, clinic_id=None)
    assert plan.plan_name == "MetLife Preferred PPO"

    # List Plans
    plan_list = await ins_api.list_plans(current_user=user, db=db, clinic_id=None)
    assert len(plan_list) >= 1


@pytest.mark.asyncio
async def test_api_patient_policies_and_verification():
    user = make_user()
    db = FakeAsyncDb()

    pol_payload = PatientInsurancePolicyCreate(
        patient_id=uuid4(),
        provider_id=uuid4(),
        policy_number="POL-9921",
        member_id="MEM-9921",
        effective_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        status=PolicyStatus.PENDING_VERIFICATION,
    )
    policy = await ins_api.create_patient_policy(payload=pol_payload, current_user=user, db=db, clinic_id=None)
    assert policy.policy_number == "POL-9921"

    # Verify policy
    v_req = PolicyVerificationRequest(is_verified=True, notes="Confirmed coverage limit via payer phone")
    verified = await ins_api.verify_patient_policy(
        policy_id=policy.id, payload=v_req, current_user=user, db=db, clinic_id=None
    )
    assert verified.status == PolicyStatus.ACTIVE


@pytest.mark.asyncio
async def test_api_preauth_and_claims():
    user = make_user()
    db = FakeAsyncDb()

    # 1. PreAuth
    pa_req = PreAuthCreate(
        patient_id=uuid4(),
        policy_id=uuid4(),
        requested_amount=12000.0,
        clinical_justification="Pulpal therapy required",
    )
    pa = await ins_api.create_preauthorization(payload=pa_req, current_user=user, db=db, clinic_id=None)
    assert pa.status == PreAuthStatus.DRAFT

    pa_up = await ins_api.update_preauthorization_status(
        preauth_id=pa.id,
        payload=PreAuthStatusUpdate(status=PreAuthStatus.APPROVED, approved_amount=10000.0),
        current_user=user,
        db=db,
        clinic_id=None,
    )
    assert pa_up.status == PreAuthStatus.APPROVED

    # 2. Claim
    cl_req = ClaimCreate(
        patient_id=uuid4(),
        policy_id=uuid4(),
        preauth_id=pa.id,
        total_claimed_amount=12000.0,
        items=[
            ClaimItemCreate(
                procedure_code="D3330",
                procedure_name="Molar Root Canal",
                tooth_number="46",
                quantity=1,
                unit_cost=12000.0,
                total_cost=12000.0,
                covered_amount=10000.0,
                patient_responsibility=2000.0,
                insurance_responsibility=10000.0,
            )
        ],
    )
    claim = await ins_api.create_claim(payload=cl_req, current_user=user, db=db, clinic_id=None)
    assert claim.claim_number.startswith("CLM-")
    assert claim.status == ClaimStatus.DRAFT

    # Update claim status
    cl_up = await ins_api.update_claim_status(
        claim_id=claim.id,
        payload=ClaimStatusUpdate(status=ClaimStatus.SUBMITTED),
        current_user=user,
        db=db,
        clinic_id=None,
    )
    assert cl_up.status == ClaimStatus.SUBMITTED


@pytest.mark.asyncio
async def test_api_reconciliations():
    user = make_user()
    claim_id = uuid4()
    claim = InsuranceClaim(
        id=claim_id,
        clinic_id=user.clinic_id,
        patient_id=uuid4(),
        policy_id=uuid4(),
        claim_number="CLM-REC-001",
        status=ClaimStatus.APPROVED,
        total_claimed_amount=10000.0,
        approved_amount=8000.0,
        paid_amount=0.0,
    )
    db = FakeAsyncDb([claim])

    rec_payload = PaymentReconciliationCreate(
        claim_id=claim_id,
        reconciliation_reference="EFT-TEST-REC",
        payment_date=date(2026, 9, 8),
        insurance_settled_amount=8000.0,
        patient_copay_due=2000.0,
        adjustment_amount=0.0,
        settlement_type=SettlementType.FULL,
    )
    rec = await ins_api.create_reconciliation(payload=rec_payload, current_user=user, db=db, clinic_id=None)
    assert rec.reconciliation_reference == "EFT-TEST-REC"
    assert rec.insurance_settled_amount == 8000.0


@pytest.mark.asyncio
async def test_api_reports():
    user = make_user()
    db = FakeAsyncDb()

    claims_report = await ins_api.get_claims_report(current_user=user, db=db, clinic_id=None)
    assert claims_report is not None
    assert isinstance(claims_report.claims, list)

    perf_report = await ins_api.get_provider_performance_report(current_user=user, db=db, clinic_id=None)
    assert perf_report is not None
    assert isinstance(perf_report.providers, list)


@pytest.mark.asyncio
async def test_api_ai_insurance_assistant():
    user = make_user()

    # 1. Audit completeness
    audit_req = ins_api.AuditCompletenessRequest(
        claim_id=uuid4(),
        procedure_codes=["D3330"],
        attached_document_types=["X_RAY"],
    )
    audit = await ins_api.audit_claim_completeness(payload=audit_req, current_user=user)
    assert audit.completeness_score > 0
    assert audit.disclaimer is not None

    # 2. Suggest coding
    coding_req = ins_api.SuggestCodingRequest(
        procedure_descriptions=["Molar root canal", "Porcelain crown"],
    )
    coding = await ins_api.suggest_coding(payload=coding_req, current_user=user)
    assert len(coding.suggestions) == 2

    # 3. Analyze rejection
    rej_req = ins_api.AnalyzeRejectionRequest(
        claim_id=uuid4(),
        denial_code="CO-16",
        denial_reason="Missing clinical documentation",
    )
    rej = await ins_api.analyze_rejection(payload=rej_req, current_user=user)
    assert rej.denial_code == "CO-16"
    assert "APPEAL" in rej.suggested_appeal_letter
