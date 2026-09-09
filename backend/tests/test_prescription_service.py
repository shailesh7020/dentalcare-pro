from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.models.prescription import (
    DosageFrequency,
    MedicineForm,
    Prescription,
    PrescriptionItem,
    PrescriptionStatus,
)
from app.models.treatment import Treatment, TreatmentStatus
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionUpdate,
)
from app.services.prescription_service import PrescriptionService


class FakeServiceDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def delete(self, item: object) -> None:
        if item in self.items:
            self.items.remove(item)

    async def flush(self) -> None:
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
            if getattr(item, "created_at", None) is None:
                item.created_at = datetime.now(UTC)
            if getattr(item, "updated_at", None) is None:
                item.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def get(self, model: type, id_: object) -> object | None:
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, statement: object) -> object:
        text = str(statement).lower()
        from types import SimpleNamespace

        # 1. Count
        if "count(" in text:
            matching = [i for i in self.items if isinstance(i, Prescription) and i.deleted_at is None]
            return SimpleNamespace(scalar_one=lambda: len(matching), scalar_one_or_none=lambda: len(matching))

        # 2. Patient
        if "from patients" in text:
            patients = [i for i in self.items if isinstance(i, Patient) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: patients[0] if patients else None,
                scalars=lambda: SimpleNamespace(all=lambda: patients),
            )

        # 3. Treatment
        if "from treatments" in text:
            treatments = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: treatments[0] if treatments else None,
                scalars=lambda: SimpleNamespace(all=lambda: treatments),
            )

        # 4. Appointment
        if "from appointments" in text:
            appointments = [i for i in self.items if isinstance(i, Appointment) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: appointments[0] if appointments else None,
                scalars=lambda: SimpleNamespace(all=lambda: appointments),
            )

        # 5. User / Dentist
        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        # 6. Prescription
        if "from prescriptions" in text:
            rxs = [i for i in self.items if isinstance(i, Prescription) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: rxs[0] if rxs else None,
                scalars=lambda: SimpleNamespace(all=lambda: rxs),
            )

        return SimpleNamespace(
            scalar_one=lambda: 0,
            scalar_one_or_none=lambda: None,
            scalars=lambda: SimpleNamespace(all=list),
        )


@pytest.fixture
def setup_clinic_data():
    clinic_id = uuid4()
    patient_id = uuid4()
    treatment_id = uuid4()
    appointment_id = uuid4()
    dentist_id = uuid4()

    dentist = User(
        id=dentist_id,
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
        clinic_id=clinic_id,
    )
    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        first_name="Riya",
        last_name="Kapoor",
        patient_number="P-2026-001",
        gender="FEMALE",
        date_of_birth=date(1995, 5, 12),
        mobile_number="9876543210",
        medical_history=MedicalHistory(allergies="Penicillin", diabetes=False),
    )
    from datetime import time

    appointment = Appointment(
        id=appointment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        chair_id=uuid4(),
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status=AppointmentStatus.CHECKED_IN,
        visit_type=VisitType.CONSULTATION,
    )
    treatment = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=appointment_id,
        dentist_id=dentist_id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Deep caries #46",
        status=TreatmentStatus.IN_PROGRESS,
    )
    return {
        "clinic_id": clinic_id,
        "patient": patient,
        "treatment": treatment,
        "appointment": appointment,
        "dentist": dentist,
    }


@pytest.mark.asyncio
async def test_create_prescription_success_and_timeline_events(setup_clinic_data):
    data = setup_clinic_data
    clinic_id = data["clinic_id"]
    patient = data["patient"]
    treatment = data["treatment"]
    appointment = data["appointment"]
    dentist = data["dentist"]

    db = FakeServiceDb([patient, treatment, appointment, dentist])
    service = PrescriptionService(db)

    payload = PrescriptionCreate(
        patient_id=patient.id,
        treatment_id=treatment.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Symptomatic irreversible pulpitis",
        notes="Root canal therapy scheduled",
        instructions="Take strictly after food",
        items=[
            PrescriptionItemCreate(
                medicine_name="Augmentin 625 Duo",
                generic_name="Amoxicillin + Potassium Clavulanate",
                strength="625 mg",
                form=MedicineForm.TABLET,
                dosage="1 tablet",
                route="Oral",
                frequency=DosageFrequency.BD,
                duration="5 days",
                quantity=10,
            )
        ],
        issue_immediately=True,
    )

    detail = await service.create_prescription(clinic_id, payload, dentist)
    assert detail.prescription_number.startswith("RX-")
    assert detail.status == PrescriptionStatus.ISSUED
    assert len(detail.items) == 1

    # Check that timeline event and audit events were added
    timeline_events = [it for it in db.added if it.__class__.__name__ == "PatientTimelineEvent"]
    assert len(timeline_events) == 1
    assert timeline_events[0].event_type == "PRESCRIPTION_ISSUED"

    audit_events = [it for it in db.added if it.__class__.__name__ == "AuditEvent"]
    assert len(audit_events) == 1
    assert audit_events[0].action == "CREATE"


@pytest.mark.asyncio
async def test_validation_duplicate_medicines_rejection(setup_clinic_data):
    data = setup_clinic_data
    clinic_id = data["clinic_id"]
    patient = data["patient"]
    treatment = data["treatment"]
    appointment = data["appointment"]
    dentist = data["dentist"]

    db = FakeServiceDb([patient, treatment, appointment, dentist])
    service = PrescriptionService(db)

    payload = PrescriptionCreate(
        patient_id=patient.id,
        treatment_id=treatment.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Deep caries",
        items=[
            PrescriptionItemCreate(
                medicine_name="Dolo 650",
                strength="650 mg",
                dosage="1 tablet",
                frequency=DosageFrequency.TDS,
                duration="3 days",
            ),
            PrescriptionItemCreate(
                medicine_name="dolo 650",  # Duplicate case-insensitive
                strength="650 mg",
                dosage="1 tablet",
                frequency=DosageFrequency.TDS,
                duration="3 days",
            ),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_prescription(clinic_id, payload, dentist)
    assert exc_info.value.status_code == 400
    assert "Duplicate medicine entry detected" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validation_empty_prescription_on_issue(setup_clinic_data):
    data = setup_clinic_data
    clinic_id = data["clinic_id"]
    patient = data["patient"]
    treatment = data["treatment"]
    appointment = data["appointment"]
    dentist = data["dentist"]

    db = FakeServiceDb([patient, treatment, appointment, dentist])
    service = PrescriptionService(db)

    payload = PrescriptionCreate(
        patient_id=patient.id,
        treatment_id=treatment.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Deep caries",
        items=[],
        issue_immediately=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_prescription(clinic_id, payload, dentist)
    assert exc_info.value.status_code == 400
    assert "Cannot issue an empty prescription" in exc_info.value.detail


@pytest.mark.asyncio
async def test_immutability_of_issued_prescription(setup_clinic_data):
    data = setup_clinic_data
    clinic_id = data["clinic_id"]
    patient = data["patient"]
    treatment = data["treatment"]
    dentist = data["dentist"]

    rx = Prescription(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        prescription_number="RX-20260908-0001",
        date=datetime.now(UTC).date(),
        diagnosis="Acute pulpitis",
        status=PrescriptionStatus.ISSUED,
        patient=patient,
        treatment=treatment,
        dentist=dentist,
    )

    db = FakeServiceDb([patient, treatment, dentist, rx])
    service = PrescriptionService(db)

    # Attempting to edit an officially ISSUED prescription must be rejected!
    update_payload = PrescriptionUpdate(diagnosis="Attempted edit")
    with pytest.raises(HTTPException) as exc_info:
        await service.update_prescription(clinic_id, rx.id, update_payload, dentist)
    assert exc_info.value.status_code == 400
    assert "locked for clinical immutability" in exc_info.value.detail


@pytest.mark.asyncio
async def test_cancellation_and_duplication_workflow(setup_clinic_data):
    data = setup_clinic_data
    clinic_id = data["clinic_id"]
    patient = data["patient"]
    treatment = data["treatment"]
    dentist = data["dentist"]

    rx = Prescription(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        prescription_number="RX-20260908-0001",
        date=datetime.now(UTC).date(),
        diagnosis="Acute pulpitis",
        status=PrescriptionStatus.ISSUED,
        items=[
            PrescriptionItem(
                id=uuid4(),
                prescription_id=uuid4(),
                medicine_name="Amoxil 500",
                strength="500 mg",
                dosage="1 cap",
                route="Oral",
                frequency=DosageFrequency.TDS,
                duration="5 days",
                quantity=15,
            )
        ],
        patient=patient,
        treatment=treatment,
        dentist=dentist,
    )

    db = FakeServiceDb([patient, treatment, data["appointment"], dentist, rx])
    service = PrescriptionService(db)

    # 1. Cancel prescription with clinical reason
    cancelled = await service.cancel_prescription(
        clinic_id, rx.id, "Patient experienced gastric upset", dentist
    )
    assert cancelled.status == PrescriptionStatus.CANCELLED
    assert cancelled.cancellation_reason == "Patient experienced gastric upset"

    # 2. Duplicate prescription into a new draft
    duplicate = await service.duplicate_prescription(clinic_id, rx.id, dentist)
    assert duplicate.status == PrescriptionStatus.DRAFT
    assert len(duplicate.items) == 1
    assert duplicate.items[0].medicine_name == "Amoxil 500"
    assert "Duplicated from RX-20260908-0001" in duplicate.notes
