from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import ai as ai_api
from app.models.ai import (
    AIAuditLog,
    AIConfiguration,
    AIRecommendation,
    AIRecommendationStatus,
)
from app.models.appointment import Appointment
from app.models.identity import Role, User
from app.models.inventory import InventoryCategory, InventoryItem
from app.models.patient import MedicalHistory, Patient
from app.models.treatment import Treatment
from app.schemas.ai import (
    AIConfigUpdate,
    AIRecommendationReview,
    ClinicalDocGenerateRequest,
    ClinicalDocType,
    MissingDocAuditRequest,
    PatientSummaryRequest,
    PrescriptionSuggestRequest,
    SchedulingRecommendationRequest,
    SOAPGenerateRequest,
    TreatmentSuggestionRequest,
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
        if "sum" in text:
            return 85000.0
        if "count" in text:
            return 25
        if "from ai_configurations" in text:
            cfgs = [i for i in self.items if isinstance(i, AIConfiguration)]
            return ScalarResult(cfgs)
        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return ScalarResult(pats)
        if "from treatments" in text:
            trts = [i for i in self.items if isinstance(i, Treatment)]
            return ScalarResult(trts)
        if "from appointments" in text:
            appts = [i for i in self.items if isinstance(i, Appointment)]
            return ScalarResult(appts)
        if "from ai_recommendations" in text:
            recs = [i for i in self.items if isinstance(i, AIRecommendation)]
            return ScalarResult(recs)
        if "from ai_audit_logs" in text:
            logs = [i for i in self.items if isinstance(i, AIAuditLog)]
            return ScalarResult(logs)
        if "from inventory_items" in text:
            invs = [i for i in self.items if isinstance(i, InventoryItem)]
            return ScalarResult(invs)
        if "from prescriptions" in text:
            return ScalarResult([])
        if "from patient_forms" in text:
            return ScalarResult([])
        return ScalarResult(self.items)


def setup_test_context():
    clinic_id = uuid4()
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@clinic.com",
        role=Role.CLINIC_ADMIN,
        first_name="Admin",
        last_name="User",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@clinic.com",
        role=Role.DENTIST,
        first_name="Dr. Priya",
        last_name="Nair",
    )
    med = MedicalHistory(
        id=uuid4(),
        patient_id=uuid4(),
        diabetes=True,
        allergies="Penicillin",
    )
    patient = Patient(
        id=med.patient_id,
        clinic_id=clinic_id,
        patient_number="P-9901",
        first_name="Aarav",
        last_name="Patel",
        mobile_number="9876543210",
        medical_history=med,
    )
    return clinic_id, admin, dentist, patient


@pytest.mark.asyncio
async def test_api_ai_config_lifecycle():
    clinic_id, admin, _dentist, _patient = setup_test_context()
    db = FakeAsyncDb()

    # 1. Get default config when none exists
    cfg_read = await ai_api.get_ai_config(clinic_id=clinic_id, actor=admin, db=db)
    assert cfg_read.clinic_id == clinic_id
    assert cfg_read.provider_type == "MOCK"
    assert cfg_read.is_active is True

    # 2. Update config
    update_payload = AIConfigUpdate(
        temperature=0.35,
        max_tokens=1024,
        clinical_guardrails_enabled=True,
    )
    updated = await ai_api.update_ai_config(payload=update_payload, clinic_id=clinic_id, actor=admin, db=db)
    assert updated.temperature == 0.35
    assert updated.max_tokens == 1024


@pytest.mark.asyncio
async def test_api_patient_summary_and_missing_docs():
    _clinic_id, _admin, dentist, patient = setup_test_context()
    db = FakeAsyncDb(items=[patient])

    # 1. Summary
    sum_req = PatientSummaryRequest(patient_id=patient.id)
    summary = await ai_api.generate_patient_summary(payload=sum_req, actor=dentist, db=db)
    assert summary.patient_id == patient.id
    assert len(summary.summary_text) > 0
    assert len(summary.risk_alerts) >= 1

    # 2. Missing docs audit
    doc_req = MissingDocAuditRequest(patient_id=patient.id)
    audit = await ai_api.audit_missing_documentation(payload=doc_req, actor=dentist, db=db)
    assert audit.patient_id == patient.id


@pytest.mark.asyncio
async def test_api_soap_generation():
    _clinic_id, _admin, dentist, patient = setup_test_context()
    db = FakeAsyncDb(items=[patient])

    req = SOAPGenerateRequest(
        patient_id=patient.id,
        clinician_notes="Caries on occlusal surface of 46, sensitive to percussion.",
    )
    draft = await ai_api.generate_soap_note(payload=req, actor=dentist, db=db)
    assert draft.subjective != ""
    assert draft.objective != ""
    assert draft.assessment != ""
    assert draft.plan != ""


@pytest.mark.asyncio
async def test_api_prescriptions_and_treatment_suggestions():
    _clinic_id, _admin, dentist, patient = setup_test_context()
    db = FakeAsyncDb(items=[patient])

    # 1. Prescriptions
    rx_req = PrescriptionSuggestRequest(
        patient_id=patient.id,
        diagnosis="Acute pericoronitis 38",
    )
    rx_res = await ai_api.suggest_prescriptions(payload=rx_req, actor=dentist, db=db)
    assert len(rx_res.suggested_items) >= 1
    assert any("penicillin" in w.lower() for w in rx_res.allergy_warnings)

    # 2. Treatment suggestion
    trt_req = TreatmentSuggestionRequest(
        patient_id=patient.id,
        tooth_number="38",
        chief_complaint="Severe pain and swelling behind lower left molar",
    )
    trt_res = await ai_api.suggest_treatment_plan(payload=trt_req, actor=dentist, db=db)
    assert trt_res.primary_recommendation.title != ""


@pytest.mark.asyncio
async def test_api_clinical_documents():
    _clinic_id, _admin, dentist, patient = setup_test_context()
    db = FakeAsyncDb(items=[patient])

    req = ClinicalDocGenerateRequest(
        patient_id=patient.id,
        document_type=ClinicalDocType.REFERRAL_LETTER,
        recipient_doctor="Dr. K. Mehta (Oral Surgeon)",
        custom_notes="Impacted third molar with recurrent pericoronitis.",
    )
    doc_res = await ai_api.generate_clinical_document(payload=req, actor=dentist, db=db)
    assert doc_res.title != ""
    assert len(doc_res.formatted_content) > 20


@pytest.mark.asyncio
async def test_api_scheduling_and_inventory():
    clinic_id, _admin, dentist, patient = setup_test_context()
    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="COMP-01",
        name="Universal Composite",
        category=InventoryCategory.CONSUMABLES.value,
        current_quantity=2,
        reorder_level=10,
        deleted_at=None,
    )
    db = FakeAsyncDb(items=[patient, item])

    # 1. Scheduling
    sched_req = SchedulingRecommendationRequest(
        patient_id=patient.id,
        procedure_name="Molar Root Canal Treatment",
    )
    sched_res = await ai_api.recommend_scheduling(payload=sched_req, actor=dentist, db=db)
    assert sched_res.recommended_duration_minutes >= 45

    # 2. Inventory Forecast
    inv_res = await ai_api.forecast_inventory(clinic_id=clinic_id, actor=dentist, db=db)
    assert len(inv_res.forecasts) >= 1


@pytest.mark.asyncio
async def test_api_recommendation_review_and_tenancy():
    clinic_id, _admin, dentist, patient = setup_test_context()
    rec_id = uuid4()
    rec = AIRecommendation(
        id=rec_id,
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        recommendation_type="SOAP_NOTE",
        status=AIRecommendationStatus.PENDING_REVIEW,
        input_context_json={"notes": "test"},
        generated_output_json={"plan": "RCT"},
        created_at=datetime.now(UTC),
    )
    db = FakeAsyncDb(items=[rec])

    # 1. List recommendations
    recs = await ai_api.list_recommendations(clinic_id=clinic_id, actor=dentist, db=db)
    assert len(recs) == 1

    # 2. Review recommendation
    review_req = AIRecommendationReview(
        status=AIRecommendationStatus.APPROVED,
        clinician_feedback="Accurate diagnosis and plan verified.",
        final_content="Final verified SOAP notes.",
    )
    reviewed = await ai_api.review_recommendation(recommendation_id=rec_id, payload=review_req, actor=dentist, db=db)
    assert reviewed.status == AIRecommendationStatus.APPROVED
    assert reviewed.clinician_feedback == "Accurate diagnosis and plan verified."

    # 3. Tenancy isolation check: User trying to access another clinic
    other_clinic_id = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await ai_api.list_recommendations(clinic_id=other_clinic_id, actor=dentist, db=db)
    assert exc_info.value.status_code == 403
