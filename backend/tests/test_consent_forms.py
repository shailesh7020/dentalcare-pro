from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.consent_form import (
    ConsentRecord,
    FormStatus,
    FormTemplate,
    FormType,
    PatientForm,
)
from app.models.identity import Clinic, Role, User
from app.models.patient import Patient
from app.schemas.consent_form import (
    ConsentRecordCreate,
    FormTemplateCreate,
    FormTemplateUpdate,
    PatientFormCreate,
    PatientFormReview,
    PatientFormSubmit,
)
from app.services.consent_form_service import ConsentFormService


class FakeConsentDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        for it in self.added:
            if getattr(it, "id", None) is None:
                it.id = uuid4()
            if getattr(it, "created_at", None) is None:
                it.created_at = datetime.now(UTC)
            if getattr(it, "updated_at", None) is None:
                it.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for it in self.items:
            if isinstance(it, model) and getattr(it, "id", None) == id_:
                return it
        return None

    async def scalar(self, stmt: object) -> object:
        res = await self.execute(stmt)
        if hasattr(res, "scalar_one_or_none"):
            return res.scalar_one_or_none()
        return None

    async def execute(self, stmt: object) -> object:
        text = str(stmt).lower()
        from types import SimpleNamespace

        if "from form_templates" in text:
            tmpls = [i for i in self.items if isinstance(i, FormTemplate) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: tmpls),
                scalar_one_or_none=lambda: tmpls[0] if tmpls else None,
            )

        if "from patient_forms" in text:
            pforms = [i for i in self.items if isinstance(i, PatientForm) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: pforms),
                scalar_one_or_none=lambda: pforms[0] if pforms else None,
            )

        if "from consent_records" in text:
            consents = [i for i in self.items if isinstance(i, ConsentRecord) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: consents),
                scalar_one_or_none=lambda: consents[0] if consents else None,
            )

        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic)]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: pats[0] if pats else None,
                scalars=lambda: SimpleNamespace(all=lambda: pats),
            )

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=list),
            scalar_one_or_none=lambda: None,
        )


@pytest.fixture
def consent_setup():
    clinic_id = uuid4()
    clinic = Clinic(id=clinic_id, name="Apex Dental Care", slug="apex-dental", is_active=True)
    doctor = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.apex@dental.com",
        first_name="Gregory",
        last_name="House",
        role=Role.DENTIST,
        is_active=True,
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        first_name="James",
        last_name="Wilson",
        patient_number="P-5501",
        mobile_number="+919876500000",
        email="wilson@clinic.com",
    )
    return clinic, doctor, patient


@pytest.mark.asyncio
async def test_form_template_lifecycle(consent_setup):
    clinic, doctor, patient = consent_setup
    db = FakeConsentDb([clinic, doctor, patient])
    service = ConsentFormService(db)

    # 1. Create template
    tmpl_payload = FormTemplateCreate(
        title="Dental Implant Surgical Consent",
        description="Risks and specifications for dental implant surgery.",
        form_type=FormType.SURGICAL_CONSENT,
        schema_json=json.dumps([{"id": "c1", "type": "checkbox", "label": "I consent to implant surgery."}]),
    )
    tmpl = await service.create_template(clinic.id, tmpl_payload)
    assert tmpl.id is not None
    assert tmpl.title == "Dental Implant Surgical Consent"

    # 2. Update template
    updated = await service.update_template(
        clinic.id, tmpl.id, FormTemplateUpdate(description="Updated risk protocol.")
    )
    assert updated.description == "Updated risk protocol."

    # 3. List templates
    all_tmpls = await service.list_templates(clinic.id)
    assert len(all_tmpls) >= 1


@pytest.mark.asyncio
async def test_patient_form_assignment_submission_and_review(consent_setup):
    clinic, doctor, patient = consent_setup
    template = FormTemplate(
        id=uuid4(),
        clinic_id=clinic.id,
        title="Medical History Form",
        form_type=FormType.MEDICAL_HISTORY,
        schema_json="[]",
        version=1,
    )
    db = FakeConsentDb([clinic, doctor, patient, template])
    service = ConsentFormService(db)

    # 1. Assign form
    assigned = await service.assign_patient_form(
        clinic.id,
        PatientFormCreate(
            patient_id=patient.id,
            template_id=template.id,
        ),
    )
    assert assigned.id is not None
    assert assigned.status == FormStatus.PENDING

    # 2. Patient submits answers
    submitted = await service.submit_patient_form(
        clinic.id,
        assigned.id,
        PatientFormSubmit(answers_json=json.dumps({"allergies": "Penicillin", "smoker": False})),
    )
    assert submitted.status == FormStatus.SUBMITTED
    assert "Penicillin" in submitted.answers_json

    # 3. Dentist reviews and approves
    reviewed = await service.review_patient_form(
        clinic.id,
        submitted.id,
        doctor.id,
        PatientFormReview(status=FormStatus.APPROVED, notes="Reviewed. No contraindications."),
    )
    assert reviewed.status == FormStatus.APPROVED
    assert reviewed.notes == "Reviewed. No contraindications."


@pytest.mark.asyncio
async def test_digital_consent_record(consent_setup):
    clinic, doctor, patient = consent_setup
    db = FakeConsentDb([clinic, doctor, patient])
    service = ConsentFormService(db)

    payload = ConsentRecordCreate(
        patient_id=patient.id,
        consent_type="EXTRACTION",
        title="Consent for Wisdom Tooth Extraction",
        content_text="I understand the risks of extraction including nerve paresthesia.",
        patient_signature="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        witness_name="Nurse Ratched",
        expires_at=date(2027, 1, 1),
    )

    consent = await service.record_consent(clinic.id, payload, ip_address="192.168.1.100")
    assert consent.id is not None
    assert consent.patient_name == f"{patient.first_name} {patient.last_name}"
    assert consent.ip_address == "192.168.1.100"
    assert consent.witness_name == "Nurse Ratched"

    # List consents
    records = await service.list_consent_records(clinic.id, patient_id=patient.id)
    assert len(records) >= 1
