from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import patients as patient_api
from app.models import Patient, Role, User
from app.schemas.patient import PatientInput, PatientUpdate


def staff() -> User:
    return User(
        id=uuid4(),
        clinic_id=uuid4(),
        email=f"staff-{uuid4()}@example.com",
        password_hash="hash",
        first_name="Staff",
        last_name="Member",
        role=Role.RECEPTIONIST,
        is_active=True,
    )


def patient(clinic_id) -> Patient:  # type: ignore[no-untyped-def]
    return Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="P-API-0001",
        first_name="Riya",
        last_name="Kapoor",
        gender="FEMALE",
        date_of_birth=date(1994, 2, 3),
        mobile_number="9876543210",
        email="riya@example.com",
        city="Mumbai",
        country="India",
        preferred_language="English",
    )


def payload() -> PatientInput:
    return PatientInput(
        first_name="Riya",
        last_name="Kapoor",
        gender="FEMALE",
        date_of_birth="1994-02-03",
        mobile_number="9876543210",
        email="riya@example.com",
    )


class StubRepository:
    def __init__(self, item: Patient) -> None:
        self.item = item

    async def list_patients(self, *_args, **_kwargs):
        return [self.item], 1  # type: ignore[no-untyped-def]

    async def histories(self, _id):
        return None, None  # type: ignore[no-untyped-def]

    async def timeline(self, *_args):
        return [
            SimpleNamespace(
                id=uuid4(),
                event_type="PATIENT_CREATED",
                title="Patient registered",
                description=None,
                created_at=datetime.now(UTC),
            )
        ]  # type: ignore[no-untyped-def]


class StubService:
    item: Patient

    def __init__(self, _db, actor: User) -> None:
        self.actor = actor
        self.clinic_id = actor.clinic_id
        self.repository = StubRepository(self.item)

    async def create(self, _payload):
        return self.item, []  # type: ignore[no-untyped-def]

    async def get(self, _id, include_deleted=False, viewed=False):
        return self.item  # type: ignore[no-untyped-def]

    async def update(self, _id, _payload):
        return self.item, []  # type: ignore[no-untyped-def]

    async def delete(self, _id):
        return None  # type: ignore[no-untyped-def]

    async def restore(self, _id):
        return self.item  # type: ignore[no-untyped-def]

    async def list_documents(self, _id):
        return []  # type: ignore[no-untyped-def]

    async def upload_document(self, **kwargs):
        return SimpleNamespace(
            id=uuid4(),
            file_name=kwargs.get("file_name", "test.pdf"),
            content_type=kwargs.get("content_type", "application/pdf"),
            document_type=kwargs.get("document_type", "DOCUMENT"),
            storage_key="test.pdf",
            created_at=datetime.now(UTC),
        )  # type: ignore[no-untyped-def]

    async def get_document(self, _patient_id, _document_id):
        return SimpleNamespace(
            id=uuid4(),
            file_name="test.pdf",
            content_type="application/pdf",
            storage_key="test.pdf",
        )  # type: ignore[no-untyped-def]


@pytest.mark.asyncio
async def test_patient_routes_map_service_results(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = staff()
    StubService.item = patient(actor.clinic_id)
    monkeypatch.setattr(patient_api, "PatientService", StubService)
    created = await patient_api.create_patient(payload(), actor, object())
    listed = await patient_api.list_patients(
        search=None,
        skip=0,
        limit=25,
        sort="created_at",
        descending=True,
        status_filter="active",
        gender=None,
        blood_group=None,
        actor=actor,
        db=object(),
    )
    searched = await patient_api.search_patients("Riya", 0, 25, actor, object())
    detail = await patient_api.get_patient(StubService.item.id, actor, object())
    updated = await patient_api.update_patient(
        StubService.item.id, PatientUpdate(notes="Verified"), actor, object()
    )
    restored = await patient_api.restore_patient(StubService.item.id, actor, object())
    timeline = await patient_api.patient_timeline(StubService.item.id, actor, object())
    docs = await patient_api.list_documents(StubService.item.id, actor, object())
    await patient_api.delete_patient(StubService.item.id, actor, object())
    assert created.patient.patient_number == "P-API-0001"
    assert listed.total == searched.total == 1
    assert detail.patient_number == "P-API-0001"
    assert updated.patient.id == restored.id
    assert timeline[0].event_type == "PATIENT_CREATED"
    assert docs == []


@pytest.mark.asyncio
async def test_patient_api_upload_and_download(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from io import BytesIO

    from fastapi import HTTPException, UploadFile

    actor = staff()
    StubService.item = patient(actor.clinic_id)
    monkeypatch.setattr(patient_api, "PatientService", StubService)

    # Mock storage on request.app.state.storage
    class FakeStorage:
        async def save_patient_upload(self, clinic_id, patient_id, file):
            return "test_doc.pdf", "/storage/test_doc.pdf"

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(storage=FakeStorage())))
    file = UploadFile(
        filename="test_doc.pdf",
        file=BytesIO(b"%PDF-1.4 test"),
        headers={"content-type": "application/pdf"},
    )
    upload_resp = await patient_api.upload_document(
        StubService.item.id,
        request,
        file,
        document_type="DOCUMENT",
        actor=actor,
        db=object(),
    )
    assert upload_resp.file_name == "test_doc.pdf"
    assert "download" in upload_resp.url

    # Test download route with real file in tmp_path
    doc_file = tmp_path / "test.pdf"
    doc_file.write_bytes(b"%PDF-1.4 content")
    fake_settings = SimpleNamespace(storage_local_path=tmp_path)
    monkeypatch.setattr(patient_api, "get_settings", lambda: fake_settings)

    download_resp = await patient_api.download_document(
        StubService.item.id,
        uuid4(),
        actor=actor,
        db=object(),
    )
    assert download_resp.status_code == 200

    # Test download 404 when file does not exist on disk
    missing_settings = SimpleNamespace(storage_local_path=tmp_path / "nonexistent")
    monkeypatch.setattr(patient_api, "get_settings", lambda: missing_settings)
    with pytest.raises(HTTPException, match="File not found"):
        await patient_api.download_document(
            StubService.item.id,
            uuid4(),
            actor=actor,
            db=object(),
        )


