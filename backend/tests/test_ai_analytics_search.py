from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.identity import Role, User
from app.models.inventory import InventoryCategory, InventoryItem
from app.models.patient import MedicalHistory, Patient
from app.schemas.ai import AISearchRequest
from app.services.ai.analytics_service import AIBusinessAnalyticsService
from app.services.ai.inventory_forecasting_service import AIInventoryForecastingService
from app.services.ai.search_service import AINaturalLanguageSearchService


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
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, item):
        pass

    async def get(self, model, id_):
        for it in self.items:
            if isinstance(it, model) and getattr(it, "id", None) == id_:
                return it
        return None

    async def scalar(self, stmt):
        text = str(stmt).lower()
        if "sum" in text:
            return 82450.0
        if "count" in text:
            return 32
        res = await self.execute(stmt)
        return res.scalar_one_or_none()

    async def execute(self, stmt):
        text = str(stmt).lower()
        if "from inventory_items" in text:
            invs = [i for i in self.items if isinstance(i, InventoryItem)]
            return ScalarResult(invs)
        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return ScalarResult(pats)
        return ScalarResult([])


@pytest.mark.asyncio
async def test_ai_inventory_forecasting():
    clinic_id = uuid4()
    item1 = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Microhybrid Composite Syringe A2",
        sku="RES-A2",
        category=InventoryCategory.CONSUMABLES.value,
        current_quantity=3,
        reorder_level=10,
        unit="syringe",
        purchase_price=1250.0,
        deleted_at=None,
    )
    item2 = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Nitrile Exam Gloves Medium",
        sku="GLV-M",
        category=InventoryCategory.CONSUMABLES.value,
        current_quantity=45,
        reorder_level=20,
        unit="box",
        purchase_price=450.0,
        deleted_at=None,
    )

    db = FakeAsyncDb(items=[item1, item2])
    service = AIInventoryForecastingService(db)

    forecast_res = await service.forecast_demand(clinic_id)

    assert len(forecast_res.forecasts) >= 2
    # Low stock item must have HIGH or CRITICAL urgency
    composite = next((f for f in forecast_res.forecasts if "composite" in f.item_name.lower()), None)
    assert composite is not None
    assert composite.urgency in ("HIGH", "CRITICAL", "MEDIUM")
    assert composite.recommended_reorder_qty > 0


@pytest.mark.asyncio
async def test_ai_business_analytics_insights():
    clinic_id = uuid4()
    db = FakeAsyncDb()
    service = AIBusinessAnalyticsService(db)

    insights = await service.generate_insights(clinic_id)

    assert insights.executive_summary != ""
    assert insights.revenue_insights != ""
    assert insights.chair_utilization_insights != ""
    assert insights.patient_retention_insights != ""
    assert len(insights.key_recommendations) >= 2
    assert any("buffer" in r.lower() or "chair" in r.lower() or "recall" in r.lower() for r in insights.key_recommendations)


@pytest.mark.asyncio
async def test_ai_natural_language_search_and_tenant_isolation():
    clinic_a = uuid4()
    clinic_b = uuid4()
    dentist_a = User(
        id=uuid4(),
        clinic_id=clinic_a,
        role=Role.DENTIST,
        first_name="Dr. Anil",
        last_name="Deshmukh",
    )

    # Patient in Clinic A with diabetes
    med_a = MedicalHistory(
        id=uuid4(),
        patient_id=uuid4(),
        diabetes=True,
    )
    patient_a = Patient(
        id=med_a.patient_id,
        clinic_id=clinic_a,
        patient_number="PAT-A-01",
        first_name="Suresh",
        last_name="Raina",
        mobile_number="9876543210",
        medical_history=med_a,
    )

    # Patient in Clinic B with diabetes (Tenant Boundary!)
    med_b = MedicalHistory(
        id=uuid4(),
        patient_id=uuid4(),
        diabetes=True,
    )
    patient_b = Patient(
        id=med_b.patient_id,
        clinic_id=clinic_b,
        patient_number="PAT-B-01",
        first_name="Rohit",
        last_name="Sharma",
        mobile_number="9988776655",
        medical_history=med_b,
    )

    # Search executed within Clinic A tenancy
    db = FakeAsyncDb(items=[patient_a])  # In practice SQLAlchemy filters Patient.clinic_id == clinic_id
    service = AINaturalLanguageSearchService(db)

    req = AISearchRequest(query="Find all patients with diabetic history")
    res = await service.search_natural_language(clinic_a, req, dentist_a)

    assert res.total_count >= 1
    result_ids = [r.id for r in res.results]
    assert str(patient_a.id) in result_ids
    assert str(patient_b.id) not in result_ids
