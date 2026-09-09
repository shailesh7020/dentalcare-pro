from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.ai import AIAuditLog, AIConfiguration, AIProviderType
from app.models.billing import Invoice
from app.models.patient import MedicalHistory, Patient
from app.models.treatment import Treatment, TreatmentProcedure, TreatmentStatus
from app.schemas.ai import (
    BillingAuditRequest,
    PrescriptionSuggestRequest,
    TreatmentSuggestionRequest,
)
from app.services.ai.billing_assistant_service import AIBillingAssistantService
from app.services.ai.prescription_assistant_service import AIPrescriptionAssistanceService
from app.services.ai.providers.mock_provider import MockDentalAIProvider


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
        res = await self.execute(stmt)
        return res.scalar_one_or_none()

    async def execute(self, stmt):
        text = str(stmt).lower()
        if "from ai_configurations" in text:
            cfgs = [i for i in self.items if isinstance(i, AIConfiguration)]
            return ScalarResult(cfgs)
        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return ScalarResult(pats)
        if "from treatments" in text:
            trts = [i for i in self.items if isinstance(i, Treatment)]
            return ScalarResult(trts)
        if "from invoices" in text:
            invs = [i for i in self.items if isinstance(i, Invoice)]
            return ScalarResult(invs)
        return ScalarResult([])


@pytest.mark.asyncio
async def test_ai_prescription_penicillin_allergy_guardrail():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    med = MedicalHistory(
        id=uuid4(),
        patient_id=patient_id,
        allergies="Severe Penicillin Anaphylaxis",
    )

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        patient_number="P-3011",
        first_name="Vikram",
        last_name="Singhania",
        medical_history=med,
    )

    cfg = AIConfiguration(
        id=uuid4(),
        clinic_id=clinic_id,
        provider_type=AIProviderType.MOCK,
        is_active=True,
    )

    db = FakeAsyncDb(items=[cfg, patient])
    service = AIPrescriptionAssistanceService(db, provider=MockDentalAIProvider())

    req = PrescriptionSuggestRequest(
        patient_id=patient_id,
        diagnosis="Acute periapical abscess with localized facial cellulitis",
    )

    response = await service.suggest_medications(clinic_id, req, dentist_id)

    # 1. Penicillin allergy guardrail check
    assert len(response.allergy_warnings) >= 1
    assert any("penicillin" in w.lower() for w in response.allergy_warnings)

    # 2. Verify no beta-lactams were suggested
    for item in response.suggested_items:
        lower_name = item.medicine_name.lower()
        assert "amoxicillin" not in lower_name
        assert "augmentin" not in lower_name
        assert "ampicillin" not in lower_name

    # 3. Verify safer alternative suggested (Clindamycin or Azithromycin)
    has_safe_alternative = any(
        "clindamycin" in it.medicine_name.lower() or "azithromycin" in it.medicine_name.lower()
        for it in response.suggested_items
    )
    assert has_safe_alternative

    # 4. AIAuditLog recorded
    audits = [i for i in db.added if isinstance(i, AIAuditLog)]
    assert len(audits) == 1
    assert any("penicillin" in f.lower() for f in audits[0].safety_flags)


@pytest.mark.asyncio
async def test_ai_treatment_suggestions():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        patient_number="P-3012",
        first_name="Kavita",
        last_name="Rao",
    )

    db = FakeAsyncDb(items=[patient])
    service = AIPrescriptionAssistanceService(db)

    # Case A: Acute throbbing tooth pain -> Root Canal & Crown recommendation
    req_pain = TreatmentSuggestionRequest(
        patient_id=patient_id,
        tooth_number="46",
        chief_complaint="Severe nocturnal throbbing toothache with lingering thermal pain",
    )
    res_pain = await service.suggest_treatment_plan(clinic_id, req_pain, dentist_id)

    assert "root canal" in res_pain.primary_recommendation.title.lower()
    assert res_pain.primary_recommendation.estimated_visits >= 1
    assert res_pain.primary_recommendation.recall_interval_days > 0
    assert len(res_pain.alternative_options) >= 1
    assert len(res_pain.primary_recommendation.pros) >= 1

    # Case B: Mild cavity -> Direct Composite restoration
    req_caries = TreatmentSuggestionRequest(
        patient_id=patient_id,
        tooth_number="15",
        chief_complaint="Mild food packing and small cavity without sensitivity",
    )
    res_caries = await service.suggest_treatment_plan(clinic_id, req_caries, dentist_id)
    assert "composite" in res_caries.primary_recommendation.title.lower()


@pytest.mark.asyncio
async def test_ai_billing_audit_unbilled_procedures():
    clinic_id = uuid4()
    patient_id = uuid4()
    treatment_id = uuid4()
    dentist_id = uuid4()

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        patient_number="P-3013",
        first_name="Sunil",
        last_name="Gavaskar",
    )

    proc1 = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Molar Endodontic Therapy",
        cost=8500.0,
    )
    proc2 = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Zirconia Crown Placement",
        cost=12000.0,
    )

    trt = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=uuid4(),
        dentist_id=dentist_id,
        treatment_number="TRT-2026-999",
        diagnosis="Irreversible Pulpitis & Crown Prep",
        status=TreatmentStatus.COMPLETED,
        procedures=[proc1, proc2],
        deleted_at=None,
    )

    # Invoices list is empty -> all procedures are unbilled
    db = FakeAsyncDb(items=[patient, trt])
    service = AIBillingAssistantService(db)

    req = BillingAuditRequest(patient_id=patient_id, treatment_id=treatment_id)
    audit = await service.audit_unbilled_items(clinic_id, req, dentist_id)

    assert audit.has_unbilled_items is True
    assert len(audit.suggestions) >= 2
    assert audit.total_unbilled_estimate >= 20000.0
    item_names = [s.name for s in audit.suggestions]
    assert "Molar Endodontic Therapy" in item_names
    assert "Zirconia Crown Placement" in item_names
