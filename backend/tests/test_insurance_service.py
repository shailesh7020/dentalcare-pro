from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.insurance import (
    CoverageType,
    InsuranceCoverageRule,
    InsurancePlan,
    InsuranceProvider,
)
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
        if "insurance_plans" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsurancePlan) and x.deleted_at is None]
            return ScalarResult(res)
        if "insurance_coverage_rules" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsuranceCoverageRule) and x.deleted_at is None]
            return ScalarResult(res)
        if "insurance_providers" in stmt_str:
            res = [x for x in self.items if isinstance(x, InsuranceProvider) and x.deleted_at is None]
            return ScalarResult(res)
        return ScalarResult(self.items)


@pytest.mark.asyncio
async def test_calculate_procedure_coverage_with_custom_rule():
    clinic_id = uuid4()
    plan_id = uuid4()

    plan = InsurancePlan(
        id=plan_id,
        clinic_id=clinic_id,
        provider_id=uuid4(),
        plan_name="Standard Dental PPO",
        plan_code="STD-PPO",
        coverage_percentage=70.0,
        annual_limit=50000.0,
    )
    rule = InsuranceCoverageRule(
        id=uuid4(),
        clinic_id=clinic_id,
        plan_id=plan_id,
        procedure_code="D3330",
        coverage_type=CoverageType.COVERED,
        coverage_percentage=90.0,
    )

    db = FakeAsyncDb([plan, rule])
    service = InsuranceService(db)

    # Cost 10,000 for D3330 (molar root canal) -> 90% covered
    covered, patient_resp, ins_resp = await service.calculate_procedure_coverage(
        clinic_id=clinic_id,
        plan_id=plan_id,
        procedure_cost=10000.0,
        procedure_code="D3330",
    )

    assert covered == 9000.0
    assert ins_resp == 9000.0
    assert patient_resp == 1000.0


@pytest.mark.asyncio
async def test_calculate_procedure_coverage_default_plan_rate():
    clinic_id = uuid4()
    plan_id = uuid4()

    plan = InsurancePlan(
        id=plan_id,
        clinic_id=clinic_id,
        provider_id=uuid4(),
        plan_name="Basic Dental Plan",
        plan_code="BASIC-50",
        coverage_percentage=50.0,
        annual_limit=20000.0,
    )

    db = FakeAsyncDb([plan])
    service = InsuranceService(db)

    # Cost 4,000 for procedure without specific rule -> 50% default
    covered, patient_resp, ins_resp = await service.calculate_procedure_coverage(
        clinic_id=clinic_id,
        plan_id=plan_id,
        procedure_cost=4000.0,
        procedure_code="D2392",
    )

    assert covered == 2000.0
    assert ins_resp == 2000.0
    assert patient_resp == 2000.0


@pytest.mark.asyncio
async def test_get_nonexistent_provider_raises_404():
    clinic_id = uuid4()
    db = FakeAsyncDb()
    service = InsuranceService(db)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_provider(clinic_id, uuid4())

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail
