from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.insurance import (
    ClaimStatus,
    InsuranceClaim,
    InsurancePreAuthorization,
    PreAuthStatus,
)
from app.schemas.insurance import ClaimStatusUpdate, PreAuthStatusUpdate
from app.services.insurance_service import InsuranceService


class ScalarResult:
    def __init__(self, values):
        self._values = list(values) if values is not None else []

    def all(self):
        return self._values

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None


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
        if "insurance_claims" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsuranceClaim) and x.deleted_at is None]
            return ScalarResult(res)
        if "insurance_preauthorizations" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePreAuthorization) and x.deleted_at is None]
            return ScalarResult(res)
        return ScalarResult(self.items)


@pytest.mark.asyncio
async def test_claim_valid_full_workflow():
    clinic_id = uuid4()
    claim_id = uuid4()

    claim = InsuranceClaim(
        id=claim_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        policy_id=uuid4(),
        claim_number="CLM-TEST-001",
        status=ClaimStatus.DRAFT,
        total_claimed_amount=8000.0,
        approved_amount=0.0,
        patient_copay_amount=0.0,
        paid_amount=0.0,
        items=[],
        audit_trail_json=[],
    )

    db = FakeAsyncDb([claim])
    service = InsuranceService(db)

    # 1. DRAFT -> SUBMITTED
    c1 = await service.update_claim_status(clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.SUBMITTED))
    assert c1.status == ClaimStatus.SUBMITTED

    # 2. SUBMITTED -> PENDING
    c2 = await service.update_claim_status(clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.PENDING))
    assert c2.status == ClaimStatus.PENDING

    # 3. PENDING -> APPROVED
    c3 = await service.update_claim_status(
        clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.APPROVED, approved_amount=6400.0, patient_copay_amount=1600.0)
    )
    assert c3.status == ClaimStatus.APPROVED
    assert c3.approved_amount == 6400.0

    # 4. APPROVED -> PAID
    c4 = await service.update_claim_status(
        clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.PAID, paid_amount=6400.0)
    )
    assert c4.status == ClaimStatus.PAID
    assert c4.paid_amount == 6400.0

    # 5. PAID -> CLOSED
    c5 = await service.update_claim_status(clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.CLOSED))
    assert c5.status == ClaimStatus.CLOSED


@pytest.mark.asyncio
async def test_claim_invalid_status_transitions_rejected():
    clinic_id = uuid4()
    claim_id = uuid4()

    claim = InsuranceClaim(
        id=claim_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        policy_id=uuid4(),
        claim_number="CLM-TEST-002",
        status=ClaimStatus.DRAFT,
        total_claimed_amount=5000.0,
        items=[],
        audit_trail_json=[],
    )

    db = FakeAsyncDb([claim])
    service = InsuranceService(db)

    # Cannot jump DRAFT -> PAID directly
    with pytest.raises(HTTPException) as exc_info:
        await service.update_claim_status(clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.PAID))
    assert exc_info.value.status_code == 400
    assert "Invalid claim status transition" in exc_info.value.detail

    # Transition to CLOSED, then try to move back to DRAFT
    claim.status = ClaimStatus.CLOSED
    with pytest.raises(HTTPException) as exc_info2:
        await service.update_claim_status(clinic_id, claim_id, ClaimStatusUpdate(status=ClaimStatus.DRAFT))
    assert exc_info2.value.status_code == 400


@pytest.mark.asyncio
async def test_preauthorization_workflow():
    clinic_id = uuid4()
    pa_id = uuid4()

    pa = InsurancePreAuthorization(
        id=pa_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        policy_id=uuid4(),
        preauth_number="PA-2026-TEST",
        status=PreAuthStatus.DRAFT,
        requested_amount=20000.0,
    )

    db = FakeAsyncDb([pa])
    service = InsuranceService(db)

    # 1. Update to SUBMITTED
    pa1 = await service.update_preauth_status(clinic_id, pa_id, PreAuthStatusUpdate(status=PreAuthStatus.SUBMITTED))
    assert pa1.status == PreAuthStatus.SUBMITTED

    # 2. Update to UNDER_REVIEW
    pa2 = await service.update_preauth_status(clinic_id, pa_id, PreAuthStatusUpdate(status=PreAuthStatus.UNDER_REVIEW))
    assert pa2.status == PreAuthStatus.UNDER_REVIEW

    # 3. Approve
    pa3 = await service.update_preauth_status(
        clinic_id, pa_id, PreAuthStatusUpdate(status=PreAuthStatus.APPROVED, approved_amount=18000.0)
    )
    assert pa3.status == PreAuthStatus.APPROVED
    assert pa3.approved_amount == 18000.0
