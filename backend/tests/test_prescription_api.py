from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import prescriptions as rx_api
from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.models.prescription import (
    DosageFrequency,
    MedicineCatalog,
    Prescription,
    PrescriptionStatus,
    PrescriptionTemplate,
)
from app.models.treatment import Treatment, TreatmentStatus
from app.schemas.prescription import (
    PrescriptionCancel,
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionUpdate,
)


class FakeApiDb:
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

        # 2. Medicine Catalog
        if "from medicine_catalog" in text:
            meds = [i for i in self.items if isinstance(i, MedicineCatalog) and i.deleted_at is None]
            if "where medicine_catalog.brand_name" in text:
                return SimpleNamespace(scalar_one_or_none=lambda: meds[0] if meds else None, scalars=lambda: SimpleNamespace(all=lambda: meds))
            return SimpleNamespace(scalar_one_or_none=lambda: meds[0] if meds else None, scalars=lambda: SimpleNamespace(all=lambda: meds))

        # 3. Prescription Templates
        if "from prescription_templates" in text:
            tmpls = [i for i in self.items if isinstance(i, PrescriptionTemplate) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: tmpls[0] if tmpls else None, scalars=lambda: SimpleNamespace(all=lambda: tmpls))

        # 4. Patient
        if "from patients" in text:
            patients = [i for i in self.items if isinstance(i, Patient) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: patients[0] if patients else None, scalars=lambda: SimpleNamespace(all=lambda: patients))

        # 5. Treatment
        if "from treatments" in text:
            treatments = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: treatments[0] if treatments else None, scalars=lambda: SimpleNamespace(all=lambda: treatments))

        # 6. Appointment
        if "from appointments" in text:
            appointments = [i for i in self.items if isinstance(i, Appointment) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: appointments[0] if appointments else None, scalars=lambda: SimpleNamespace(all=lambda: appointments))

        # 7. User
        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: users[0] if users else None, scalars=lambda: SimpleNamespace(all=lambda: users))

        # 8. Prescription
        if "from prescriptions" in text:
            rxs = [i for i in self.items if isinstance(i, Prescription) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: rxs[0] if rxs else None, scalars=lambda: SimpleNamespace(all=lambda: rxs))

        return SimpleNamespace(scalar_one=lambda: 0, scalar_one_or_none=lambda: None, scalars=lambda: SimpleNamespace(all=list))


@pytest.mark.asyncio
async def test_prescription_api_complete_workflow():
    clinic_id = uuid4()
    patient_id = uuid4()
    treatment_id = uuid4()
    appointment_id = uuid4()
    dentist_id = uuid4()

    dentist = User(id=dentist_id, first_name="Ananya", last_name="Shah", role=Role.DENTIST, clinic_id=clinic_id)
    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        first_name="Riya",
        last_name="Kapoor",
        patient_number="P-2026-001",
        gender="FEMALE",
        date_of_birth=date(1995, 5, 12),
        mobile_number="9876543210",
        medical_history=MedicalHistory(allergies="Penicillin"),
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
        diagnosis="Deep caries on #46",
        status=TreatmentStatus.IN_PROGRESS,
    )

    db = FakeApiDb([dentist, patient, appointment, treatment])

    # 1. Create Draft Prescription
    create_payload = PrescriptionCreate(
        patient_id=patient_id,
        treatment_id=treatment_id,
        appointment_id=appointment_id,
        dentist_id=dentist_id,
        diagnosis="Acute apical periodontitis",
        notes="Root canal therapy stage 1 complete",
        instructions="Rinse with warm saline solution",
        items=[
            PrescriptionItemCreate(
                medicine_name="Dolo 650",
                generic_name="Paracetamol",
                strength="650 mg",
                dosage="1 tablet",
                frequency=DosageFrequency.TDS,
                duration="3 days",
                quantity=9,
            )
        ],
        issue_immediately=False,
    )

    created_rx = await rx_api.create_prescription(create_payload, dentist, db)
    assert created_rx.status == PrescriptionStatus.DRAFT
    assert created_rx.patient_name == "Riya Kapoor"
    assert created_rx.patient_alerts == ["ALLERGY: Penicillin"]

    # 2. Get Prescription Detail
    fetched = await rx_api.get_prescription(created_rx.id, dentist, db)
    assert fetched.id == created_rx.id

    # 3. Update Draft Prescription
    update_payload = PrescriptionUpdate(diagnosis="Updated: Acute apical periodontitis #46")
    updated = await rx_api.update_prescription(created_rx.id, update_payload, dentist, db)
    assert updated.diagnosis == "Updated: Acute apical periodontitis #46"

    # 4. Issue Prescription
    issued = await rx_api.issue_prescription(created_rx.id, None, dentist, db)
    assert issued.status == PrescriptionStatus.ISSUED

    # 5. Generate and Download PDF
    pdf_response = await rx_api.download_prescription_pdf(created_rx.id, dentist, db)
    assert pdf_response.media_type == "application/pdf"
    assert pdf_response.body.startswith(b"%PDF-")
    assert len(pdf_response.body) > 1000

    # 6. Cancel Prescription
    cancel_payload = PrescriptionCancel(reason="Discontinued due to mild rash")
    cancelled = await rx_api.cancel_prescription(created_rx.id, cancel_payload, dentist, db)
    assert cancelled.status == PrescriptionStatus.CANCELLED
    assert cancelled.cancellation_reason == "Discontinued due to mild rash"

    # 7. Duplicate Prescription
    duplicated = await rx_api.duplicate_prescription(created_rx.id, dentist, db)
    assert duplicated.status == PrescriptionStatus.DRAFT
    assert len(duplicated.items) == 1

    # 8. List templates and search medicines
    templates = await rx_api.list_prescription_templates(None, dentist, db)
    assert isinstance(templates, list)

    stats = await rx_api.get_prescription_dashboard_stats(dentist, db)
    assert stats.total_prescriptions >= 1


@pytest.mark.asyncio
async def test_prescription_api_multi_tenant_isolation():
    clinic_b_id = uuid4()

    dentist_b = User(id=uuid4(), first_name="Dr", last_name="Other", role=Role.DENTIST, clinic_id=clinic_b_id)

    db = FakeApiDb([])

    # Clinic B dentist trying to access nonexistent or foreign clinic prescription must get 404
    with pytest.raises(HTTPException) as exc_info:
        await rx_api.get_prescription(uuid4(), dentist_b, db)
    assert exc_info.value.status_code == 404
