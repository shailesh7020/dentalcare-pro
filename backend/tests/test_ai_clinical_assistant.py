from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.ai import AIAuditLog, AIConfiguration, AIProviderType
from app.models.appointment import Appointment
from app.models.consent_form import FormStatus, PatientForm
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.models.treatment import Treatment
from app.schemas.ai import PatientSummaryRequest, RiskSeverity
from app.services.ai.clinical_assistant_service import AIClinicalAssistantService
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
        if "from patient_forms" in text:
            pfs = [i for i in self.items if isinstance(i, PatientForm)]
            return ScalarResult(pfs)
        if "from appointments" in text:
            appts = [i for i in self.items if isinstance(i, Appointment)]
            return ScalarResult(appts)
        if "from prescriptions" in text:
            return ScalarResult([])
        return ScalarResult([])


@pytest.mark.asyncio
async def test_clinical_assistant_summary_with_allergy_and_diabetes():
    clinic_id = uuid4()
    patient_id = uuid4()
    doctor_id = uuid4()

    doctor = User(
        id=doctor_id,
        clinic_id=clinic_id,
        email="doctor@clinic.com",
        role=Role.DENTIST,
        first_name="Dr. Sameer",
        last_name="Joshi",
    )

    med = MedicalHistory(
        id=uuid4(),
        patient_id=patient_id,
        diabetes=True,
        allergies="Penicillin",
        additional_notes="Anaphylactic reaction to amoxicillin in 2021",
    )

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        patient_number="P-1002",
        first_name="Anita",
        last_name="Sharma",
        medical_history=med,
    )

    cfg = AIConfiguration(
        id=uuid4(),
        clinic_id=clinic_id,
        provider_type=AIProviderType.MOCK,
        model_name="mock-dental-clinical-v1",
        is_active=True,
    )

    db = FakeAsyncDb(items=[cfg, patient])
    service = AIClinicalAssistantService(db, provider=MockDentalAIProvider())

    req = PatientSummaryRequest(patient_id=patient_id)
    summary = await service.summarize_patient_history(req, doctor)

    assert summary.patient_id == patient_id
    assert summary.patient_name == "Anita Sharma"
    assert len(summary.summary_text) > 20
    assert summary.recommended_recall_months in (3, 6, 12)

    # Risk alerts verification: Penicillin high risk & Diabetic risk
    allergy_alerts = [r for r in summary.risk_alerts if "penicillin" in r.title.lower() or "allergy" in r.category.lower()]
    assert len(allergy_alerts) >= 1
    assert any(r.severity == RiskSeverity.HIGH for r in allergy_alerts)

    diabetes_alerts = [r for r in summary.risk_alerts if "diabet" in r.title.lower() or "systemic" in r.category.lower()]
    assert len(diabetes_alerts) >= 1

    # AIAuditLog verification
    audit_logs = [item for item in db.added if isinstance(item, AIAuditLog)]
    assert len(audit_logs) >= 1
    log = audit_logs[0]
    assert log.patient_id == patient_id
    assert log.clinic_id == clinic_id
    assert log.user_id == doctor_id
    assert log.tokens_completion > 0
    assert log.request_id.startswith("AI-SUM-")


@pytest.mark.asyncio
async def test_clinical_assistant_missing_documentation_detection():
    clinic_id = uuid4()
    patient_id = uuid4()

    # 1. Treatment without adequate clinical notes
    trt_sparse = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=uuid4(),
        dentist_id=uuid4(),
        treatment_number="TRT-001",
        diagnosis="Irreversible Pulpitis",
        treatment_plan="Root Canal Therapy Tooth 16",
        clinical_notes="",  # Missing notes!
        deleted_at=None,
    )

    # 2. Pending consent form
    pending_form = PatientForm(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        template_id=uuid4(),
        status=FormStatus.PENDING,
        deleted_at=None,
    )

    db = FakeAsyncDb(items=[trt_sparse, pending_form])
    service = AIClinicalAssistantService(db)

    audit_result = await service.detect_missing_documentation(patient_id, clinic_id)

    assert audit_result.patient_id == patient_id
    assert len(audit_result.missing_items) >= 1
    assert any("notes" in item.lower() for item in audit_result.missing_items)
    assert len(audit_result.unsigned_consents) >= 1
    assert any("consent" in item.lower() for item in audit_result.unsigned_consents)
