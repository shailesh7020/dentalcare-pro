from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.ai import (
    AIAuditLog,
    AIConfiguration,
    AIProviderType,
    AIRecommendation,
    AIRecommendationStatus,
)
from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.patient import Patient
from app.models.treatment import Treatment, TreatmentStatus
from app.schemas.ai import SOAPGenerateRequest, SOAPSaveRequest
from app.services.ai.providers.mock_provider import MockDentalAIProvider
from app.services.ai.soap_service import AISOAPNoteService


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
        if "from appointments" in text:
            appts = [i for i in self.items if isinstance(i, Appointment)]
            return ScalarResult(appts)
        if "from ai_recommendations" in text:
            recs = [i for i in self.items if isinstance(i, AIRecommendation)]
            return ScalarResult(recs)
        return ScalarResult([])


@pytest.mark.asyncio
async def test_ai_soap_note_draft_generation():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()
    appt_id = uuid4()

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        patient_number="P-2001",
        first_name="Rohan",
        last_name="Mehta",
    )

    appt = Appointment(
        id=appt_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        chair_id=uuid4(),
        appointment_number="APT-001",
        date=datetime.now(UTC).date(),
        start_time=datetime.now(UTC).time(),
        end_time=datetime.now(UTC).time(),
        status=AppointmentStatus.IN_TREATMENT,
        visit_type=VisitType.CONSULTATION,
        chief_complaint="Throbbing pain on lower left molar with cold sensitivity",
    )

    cfg = AIConfiguration(
        id=uuid4(),
        clinic_id=clinic_id,
        provider_type=AIProviderType.MOCK,
        is_active=True,
    )

    db = FakeAsyncDb(items=[cfg, patient, appt])
    service = AISOAPNoteService(db, provider=MockDentalAIProvider())

    req = SOAPGenerateRequest(
        patient_id=patient_id,
        appointment_id=appt_id,
        clinician_notes="Cold test yields prolonged response (>10s). Percussion mildly sensitive.",
    )

    draft = await service.generate_soap_draft(clinic_id, req, dentist_id)

    assert draft.subjective != ""
    assert draft.objective != ""
    assert draft.assessment != ""
    assert draft.plan != ""
    assert "advisory" in draft.safety_disclaimer.lower() or "clinician must review" in draft.safety_disclaimer.lower()

    # Verify AI recommendation was queued
    recs = [i for i in db.added if isinstance(i, AIRecommendation)]
    assert len(recs) == 1
    assert recs[0].recommendation_type == "SOAP_NOTE"
    assert recs[0].status == AIRecommendationStatus.PENDING_REVIEW

    # Verify AIAuditLog
    audits = [i for i in db.added if isinstance(i, AIAuditLog)]
    assert len(audits) == 1
    assert audits[0].user_id == dentist_id


@pytest.mark.asyncio
async def test_ai_soap_note_save_to_treatment():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()
    treatment_id = uuid4()

    trt = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=uuid4(),
        dentist_id=dentist_id,
        treatment_number="TRT-2026-009",
        diagnosis="Irreversible Pulpitis Tooth 36",
        status=TreatmentStatus.IN_PROGRESS,
    )

    pending_rec = AIRecommendation(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        treatment_id=treatment_id,
        recommendation_type="SOAP_NOTE",
        status=AIRecommendationStatus.PENDING_REVIEW,
    )

    db = FakeAsyncDb(items=[trt, pending_rec])
    service = AISOAPNoteService(db)

    save_req = SOAPSaveRequest(
        treatment_id=treatment_id,
        subjective="Patient reports spontaneous pain that wakes them at night.",
        objective="Tooth #36 exhibits lingering pain to Endo-Ice for 18 seconds.",
        assessment="Symptomatic irreversible pulpitis on tooth #36.",
        plan="Proceed with root canal therapy under rubber dam isolation.",
    )

    updated_trt = await service.save_soap_to_treatment(clinic_id, save_req, dentist_id)

    # Treatment structured columns updated
    assert updated_trt.soap_subjective == save_req.subjective
    assert updated_trt.soap_objective == save_req.objective
    assert updated_trt.soap_assessment == save_req.assessment
    assert updated_trt.soap_plan == save_req.plan
    assert "CLINICIAN SOAP NOTE" in updated_trt.clinical_notes

    # Recommendation updated to APPROVED
    assert pending_rec.status == AIRecommendationStatus.APPROVED
    assert pending_rec.reviewed_by_id == dentist_id
