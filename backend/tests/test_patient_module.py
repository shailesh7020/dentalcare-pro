from datetime import date
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models import Patient, Role, User
from app.schemas.patient import PatientInput, PatientUpdate
from app.services.patient_service import PatientService


class FakeDb:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0

    def add(self, item: object) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _item: object) -> None:
        return None


class FakePatientRepository:
    def __init__(
        self,
        patient: Patient | None = None,
        duplicates: list[Patient] | None = None,
        medical_history: object | None = None,
        dental_history: object | None = None,
        documents: list[object] | None = None,
    ) -> None:
        self.patient = patient
        self.duplicate_patients = duplicates or []
        self.medical_history = medical_history
        self.dental_history = dental_history
        self.doc_items = documents or []

    async def get(self, _clinic_id, _patient_id, _include_deleted=False):  # type: ignore[no-untyped-def]
        return self.patient

    async def duplicates(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        return self.duplicate_patients

    async def histories(self, _patient_id):  # type: ignore[no-untyped-def]
        return self.medical_history, self.dental_history

    async def timeline(self, *_args):  # type: ignore[no-untyped-def]
        return []

    async def documents(self, *_args):  # type: ignore[no-untyped-def]
        return self.doc_items

    async def get_document(self, _clinic_id, _patient_id, document_id):  # type: ignore[no-untyped-def]
        for doc in self.doc_items:
            if getattr(doc, "id", None) == document_id:
                return doc
        return None


def actor(clinic_id=None) -> User:  # type: ignore[no-untyped-def]
    return User(
        id=uuid4(),
        clinic_id=clinic_id or uuid4(),
        email=f"admin-{uuid4()}@example.com",
        password_hash="hash",
        first_name="Admin",
        last_name="User",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )


def payload(**overrides: object) -> PatientInput:
    values: dict[str, object] = {
        "first_name": "Asha",
        "last_name": "Sharma",
        "gender": "FEMALE",
        "date_of_birth": "1990-01-02",
        "mobile_number": "9876543210",
        "email": "asha@example.com",
    }
    values.update(overrides)
    return PatientInput(**values)


@pytest.mark.asyncio
async def test_create_patient_is_clinic_scoped_audited_and_timeline_backed() -> None:
    db = FakeDb()
    staff = actor()
    service = PatientService(db, staff)
    service.repository = FakePatientRepository()
    patient, warnings = await service.create(
        payload(
            medical_history={"diabetes": True}, dental_history={"chief_complaint": "Sensitivity"}
        )
    )
    assert patient.clinic_id == staff.clinic_id
    assert patient.patient_number.startswith("P-")
    assert warnings == []
    assert db.commits == 1
    assert {type(item).__name__ for item in db.added} >= {
        "Patient",
        "MedicalHistory",
        "DentalHistory",
        "AuditEvent",
        "PatientTimelineEvent",
    }


@pytest.mark.asyncio
async def test_duplicate_detection_returns_field_specific_warnings() -> None:
    db = FakeDb()
    staff = actor()
    matching = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-001",
        first_name="Old",
        last_name="Patient",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
        email="asha@example.com",
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(duplicates=[matching])
    warnings = await service.duplicates(payload())
    assert {warning.field for warning in warnings} == {"mobile_number", "email"}


@pytest.mark.asyncio
async def test_soft_delete_and_restore_keep_record_in_clinic() -> None:
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-002",
        first_name="Asha",
        last_name="Sharma",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
    )
    repository = FakePatientRepository(patient=patient)
    service = PatientService(db, staff)
    service.repository = repository
    await service.delete(patient.id)
    assert patient.deleted_at is not None
    await service.restore(patient.id)
    assert patient.deleted_at is None
    assert db.commits == 2


@pytest.mark.asyncio
async def test_update_patient_changes_only_supplied_fields_and_writes_timeline() -> None:
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-003",
        first_name="Asha",
        last_name="Sharma",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(patient=patient)
    updated, warnings = await service.update(
        patient.id, PatientUpdate(notes="Reviewed at reception")
    )
    assert updated.notes == "Reviewed at reception"
    assert warnings == []
    assert {type(item).__name__ for item in db.added} >= {"AuditEvent", "PatientTimelineEvent"}


@pytest.mark.asyncio
async def test_get_patient_enforces_clinic_scoped_not_found() -> None:
    service = PatientService(FakeDb(), actor())
    service.repository = FakePatientRepository()
    with pytest.raises(HTTPException, match="Patient not found"):
        await service.get(uuid4())


@pytest.mark.asyncio
async def test_patient_service_blocks_users_without_a_clinic() -> None:
    staff = actor()
    staff.clinic_id = None
    with pytest.raises(HTTPException, match="clinic context"):
        PatientService(FakeDb(), staff)


@pytest.mark.asyncio
async def test_get_patient_viewed_records_audit() -> None:
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-004",
        first_name="Anita",
        last_name="Roy",
        gender="FEMALE",
        date_of_birth=date(1995, 5, 5),
        mobile_number="9876543210",
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(patient=patient)
    result = await service.get(patient.id, viewed=True)
    assert result.id == patient.id
    assert db.commits == 1
    assert any(getattr(item, "action", None) == "PATIENT_VIEWED" for item in db.added)


@pytest.mark.asyncio
async def test_duplicate_detection_warns_on_aadhaar() -> None:
    db = FakeDb()
    staff = actor()
    matching = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-005",
        first_name="Old",
        last_name="Patient",
        gender="MALE",
        date_of_birth=date(1985, 3, 3),
        mobile_number="9123456780",
        aadhaar_number="123456789012",
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(duplicates=[matching])
    warnings = await service.duplicates(payload(aadhaar_number="123456789012", mobile_number="9999999999"))
    assert any(w.field == "aadhaar_number" for w in warnings)


@pytest.mark.asyncio
async def test_update_patient_with_existing_and_new_histories() -> None:
    from app.models import DentalHistory, MedicalHistory
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-006",
        first_name="Kavita",
        last_name="Nair",
        gender="FEMALE",
        date_of_birth=date(1992, 4, 4),
        mobile_number="9876543210",
    )
    med = MedicalHistory(patient_id=patient.id, diabetes=False)
    dental = DentalHistory(patient_id=patient.id, flossing_habit=False)
    # First update with existing medical and dental histories
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(patient=patient, medical_history=med, dental_history=dental)
    await service.update(
        patient.id,
        PatientUpdate(
            medical_history={"diabetes": True, "allergies": "Penicillin"},
            dental_history={"flossing_habit": True, "chief_complaint": "Toothache"},
        ),
    )
    assert med.diabetes is True
    assert dental.flossing_habit is True

    # Second update where histories do not exist yet (creates them)
    service_fresh = PatientService(db, staff)
    service_fresh.repository = FakePatientRepository(patient=patient, medical_history=None, dental_history=None)
    await service_fresh.update(
        patient.id,
        PatientUpdate(
            medical_history={"hypertension": True},
            dental_history={"grinding": True},
        ),
    )
    assert any(isinstance(item, MedicalHistory) for item in db.added)
    assert any(isinstance(item, DentalHistory) for item in db.added)


@pytest.mark.asyncio
async def test_restore_fails_if_already_active() -> None:
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-007",
        first_name="Active",
        last_name="Patient",
        gender="MALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
        deleted_at=None,
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(patient=patient)
    with pytest.raises(HTTPException, match="already active"):
        await service.restore(patient.id)


@pytest.mark.asyncio
async def test_patient_documents_and_photo_upload() -> None:
    from app.models import PatientDocument
    db = FakeDb()
    staff = actor()
    patient = Patient(
        id=uuid4(),
        clinic_id=staff.clinic_id,
        patient_number="P-TEST-008",
        first_name="Doc",
        last_name="User",
        gender="FEMALE",
        date_of_birth=date(1995, 1, 1),
        mobile_number="9876543210",
    )
    existing_doc = PatientDocument(
        id=uuid4(),
        patient_id=patient.id,
        clinic_id=staff.clinic_id,
        file_name="consent.pdf",
        content_type="application/pdf",
        storage_key="patients/key.pdf",
        document_type="CONSENT",
    )
    service = PatientService(db, staff)
    service.repository = FakePatientRepository(patient=patient, documents=[existing_doc])
    docs = await service.list_documents(patient.id)
    assert len(docs) == 1
    found = await service.get_document(patient.id, existing_doc.id)
    assert found.id == existing_doc.id

    with pytest.raises(HTTPException, match="Document not found"):
        await service.get_document(patient.id, uuid4())

    # Test photo upload
    uploaded = await service.upload_document(
        patient.id,
        file_name="avatar.jpg",
        content_type="image/jpeg",
        storage_key="patients/avatar.jpg",
        url="/storage/avatar.jpg",
        document_type="PHOTO",
    )
    assert patient.photo_url == "/storage/avatar.jpg"
    assert uploaded.file_name == "avatar.jpg"
    assert any(getattr(item, "action", None) == "PATIENT_DOCUMENT_UPLOADED" for item in db.added)


def test_patient_input_rejects_future_dob_and_invalid_contacts() -> None:
    with pytest.raises(ValueError):
        payload(date_of_birth="2999-01-01")
    with pytest.raises(ValueError):
        payload(alternate_mobile="9876543210")


def test_patient_update_is_partial() -> None:
    update = PatientUpdate(notes="Updated after consultation")
    assert update.model_dump(exclude_unset=True) == {"notes": "Updated after consultation"}
    # Test date validator on update
    with pytest.raises(ValueError):
        PatientUpdate(date_of_birth="2999-01-01")

