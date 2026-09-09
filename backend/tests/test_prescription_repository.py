from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.models.prescription import (
    DosageFrequency,
    MedicineCatalog,
    MedicineForm,
    Prescription,
    PrescriptionStatus,
    PrescriptionTemplate,
    TemplateCategory,
)
from app.models.treatment import Treatment
from app.repositories.prescription_repository import PrescriptionRepository
from app.schemas.prescription import (
    MedicineCatalogCreate,
    PrescriptionCreate,
    PrescriptionItemCreate,
    PrescriptionTemplateCreate,
    PrescriptionTemplateItem,
    PrescriptionUpdate,
)


class FakePrescriptionDb:
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

        # 1. Count queries
        if "count(" in text:
            if "from prescriptions" in text:
                matching = [i for i in self.items if isinstance(i, Prescription) and i.deleted_at is None]
                if "status =" in text:
                    for st in ["issued", "draft", "cancelled"]:
                        if f"status = '{st}'" in text or f"status = {st}" in text:
                            matching = [i for i in matching if i.status.lower() == st]
                return SimpleNamespace(
                    scalar_one=lambda: len(matching),
                    scalar_one_or_none=lambda: len(matching),
                )
            return SimpleNamespace(scalar_one=lambda: 0, scalar_one_or_none=lambda: 0)

        # 2. Medicine catalog queries
        if "from medicine_catalog" in text:
            meds = [i for i in self.items if isinstance(i, MedicineCatalog) and i.deleted_at is None]
            if "where medicine_catalog.brand_name" in text:
                # Find specific brand name for seeding checks
                for m in meds:
                    if m.brand_name.lower() in text:
                        return SimpleNamespace(
                            scalar_one_or_none=lambda m=m: m,
                            scalars=lambda m=m: SimpleNamespace(all=lambda: [m]),
                        )
                return SimpleNamespace(
                    scalar_one_or_none=lambda: None,
                    scalars=lambda: SimpleNamespace(all=list),
                )
            return SimpleNamespace(
                scalar_one_or_none=lambda: meds[0] if meds else None,
                scalars=lambda: SimpleNamespace(all=lambda: meds),
            )

        # 3. Prescription template queries
        if "from prescription_templates" in text:
            templates = [i for i in self.items if isinstance(i, PrescriptionTemplate) and i.deleted_at is None]
            if "where prescription_templates.name" in text:
                for t in templates:
                    if t.name.lower() in text:
                        return SimpleNamespace(
                            scalar_one_or_none=lambda t=t: t,
                            scalars=lambda t=t: SimpleNamespace(all=lambda: [t]),
                        )
                return SimpleNamespace(
                    scalar_one_or_none=lambda: None,
                    scalars=lambda: SimpleNamespace(all=list),
                )
            return SimpleNamespace(
                scalar_one_or_none=lambda: templates[0] if templates else None,
                scalars=lambda: SimpleNamespace(all=lambda: templates),
            )

        # 4. Prescription queries
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


@pytest.mark.asyncio
async def test_generate_prescription_number():
    clinic_id = uuid4()
    db = FakePrescriptionDb()
    repo = PrescriptionRepository(db)

    rx_number = await repo.generate_prescription_number(clinic_id)
    assert rx_number.startswith("RX-")
    today_str = datetime.now(UTC).strftime("%Y%m%d")
    assert f"RX-{today_str}-0001" == rx_number


@pytest.mark.asyncio
async def test_seed_and_search_medicines():
    db = FakePrescriptionDb()
    repo = PrescriptionRepository(db)

    seeded = await repo.seed_standard_medicines()
    assert seeded >= 16

    meds = await repo.search_medicines()
    assert len(meds) >= 16

    # Test creating custom clinic medicine
    clinic_id = uuid4()
    actor = User(id=uuid4(), first_name="Dr", last_name="Dentist", role=Role.DENTIST, clinic_id=clinic_id)
    custom_payload = MedicineCatalogCreate(
        generic_name="Mupirocin 2%",
        brand_name="Bactroban Ointment",
        strength="2% w/w",
        form=MedicineForm.CREAM,
        category="Topical Antibiotic",
        default_route="Topical",
        default_frequency=DosageFrequency.BD,
        default_duration="7 days",
    )
    custom_med = await repo.create_medicine(clinic_id, custom_payload, actor)
    assert custom_med.brand_name == "Bactroban Ointment"
    assert custom_med.clinic_id == clinic_id


@pytest.mark.asyncio
async def test_seed_and_list_templates():
    db = FakePrescriptionDb()
    repo = PrescriptionRepository(db)

    seeded = await repo.seed_standard_templates()
    assert seeded >= 5

    templates = await repo.list_templates()
    assert len(templates) >= 5

    # Test creating custom template
    clinic_id = uuid4()
    actor = User(id=uuid4(), first_name="Dr", last_name="Dentist", role=Role.DENTIST, clinic_id=clinic_id)
    custom_tmpl_payload = PrescriptionTemplateCreate(
        name="Custom Implant Surgical Pack",
        category=TemplateCategory.IMPLANT,
        description="Clinic protocol for surgical implant placement",
        default_items=[
            PrescriptionTemplateItem(
                medicine_name="Augmentin 625 Duo",
                strength="625 mg",
                dosage="1 tablet",
                frequency="BD",
                duration="5 days",
                quantity=10,
            )
        ],
    )
    tmpl = await repo.create_template(clinic_id, custom_tmpl_payload, actor)
    assert tmpl.name == "Custom Implant Surgical Pack"
    assert len(tmpl.default_items) == 1


@pytest.mark.asyncio
async def test_prescription_lifecycle_and_schema_mapping():
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
        medical_history=MedicalHistory(allergies="Penicillin allergy", diabetes=False),
    )
    treatment = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=appointment_id,
        dentist_id=dentist_id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Deep dentinal caries on #46",
    )

    db = FakePrescriptionDb([dentist, patient, treatment])
    repo = PrescriptionRepository(db)

    # 1. Create Draft Prescription
    create_payload = PrescriptionCreate(
        patient_id=patient_id,
        treatment_id=treatment_id,
        appointment_id=appointment_id,
        dentist_id=dentist_id,
        diagnosis="Severe pulpitis #46",
        notes="Pre-endodontic medication",
        instructions="Take strictly after food",
        follow_up_date=date(2026, 9, 15),
        items=[
            PrescriptionItemCreate(
                medicine_name="Dolo 650",
                generic_name="Paracetamol",
                brand_name="Dolo",
                strength="650 mg",
                form=MedicineForm.TABLET,
                dosage="1 tablet",
                route="Oral",
                frequency=DosageFrequency.TDS,
                duration="3 days",
                quantity=9,
                timing="Morning - Afternoon - Night",
                food_instructions="After food",
            )
        ],
        issue_immediately=False,
    )

    rx = await repo.create(clinic_id, create_payload, dentist, "RX-20260908-0001")
    assert rx.prescription_number == "RX-20260908-0001"
    assert rx.status == PrescriptionStatus.DRAFT
    assert len(rx.items) == 1

    # Link relations in memory for schema testing
    rx.patient = patient
    rx.treatment = treatment
    rx.dentist = dentist

    # 2. Test Detail Schema
    detail = repo.to_detail_schema(rx)
    assert detail.patient_name == "Riya Kapoor"
    assert detail.patient_alerts == ["ALLERGY: Penicillin allergy"]
    assert detail.dentist_name == "Dr. Ananya Shah"
    assert detail.treatment_number == "TRT-20260908-0001"
    assert len(detail.items) == 1
    assert detail.items[0].medicine_name == "Dolo 650"

    # 3. Update Draft Prescription
    update_payload = PrescriptionUpdate(
        instructions="Rinse with warm saline",
        items=[
            PrescriptionItemCreate(
                medicine_name="Zerodol-P",
                generic_name="Aceclofenac + Paracetamol",
                strength="100 mg + 325 mg",
                form=MedicineForm.TABLET,
                dosage="1 tablet",
                route="Oral",
                frequency=DosageFrequency.BD,
                duration="3 days",
                quantity=6,
            )
        ],
    )
    updated_rx = await repo.update(rx, update_payload, dentist)
    assert updated_rx.instructions == "Rinse with warm saline"
    assert updated_rx.version == 2
    assert len(updated_rx.items) == 1
    assert updated_rx.items[0].medicine_name == "Zerodol-P"

    # 4. Issue Prescription
    issued_rx = await repo.issue(rx, dentist)
    assert issued_rx.status == PrescriptionStatus.ISSUED
    assert issued_rx.issued_at is not None

    # 5. Cancel Prescription
    cancelled_rx = await repo.cancel(rx, "Patient reported allergy flareup", dentist)
    assert cancelled_rx.status == PrescriptionStatus.CANCELLED
    assert cancelled_rx.cancellation_reason == "Patient reported allergy flareup"

    # 6. Soft Delete
    await repo.soft_delete(rx, dentist)
    assert rx.deleted_at is not None
