from datetime import date
from uuid import uuid4

import pytest

from app.models import Patient
from app.repositories.patient_repository import PatientRepository


class ScalarRows:
    def __init__(self, values):
        self.values = values  # type: ignore[no-untyped-def]

    def all(self):
        return self.values  # type: ignore[no-untyped-def]


class FakeDb:
    def __init__(self, patient: Patient) -> None:
        self.patient = patient
        self.scalar_values = [patient, 1]

    async def scalar(self, _query):
        return self.scalar_values.pop(0) if self.scalar_values else None

    async def scalars(self, query):
        if hasattr(query, "whereclause") and query.whereclause is not None:
            text_clause = str(query.whereclause).lower()
            if "false" in text_clause or "0 = 1" in text_clause:
                return ScalarRows([])
        return ScalarRows([self.patient])  # type: ignore[no-untyped-def]

    async def get(self, _model, _id):
        return None  # type: ignore[no-untyped-def]


def patient() -> Patient:
    return Patient(
        id=uuid4(),
        clinic_id=uuid4(),
        patient_number="P-REPO-001",
        first_name="Nila",
        last_name="Das",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
        email="nila@example.com",
        aadhaar_number="123456789012",
    )


@pytest.mark.asyncio
async def test_repository_applies_clinic_scoped_get_list_duplicate_and_timeline_queries() -> None:
    item = patient()
    repository = PatientRepository(FakeDb(item))
    assert await repository.get(item.clinic_id, item.id) == item
    items, total = await repository.list_patients(
        item.clinic_id, "Nila", 0, 25, "name", True, status="active", gender="FEMALE", blood_group="A+"
    )
    assert items == [item] and total == 1
    # Test archived and all status branches
    archived_items, _ = await repository.list_patients(item.clinic_id, status="archived")
    all_items, _ = await repository.list_patients(item.clinic_id, status="all")
    assert len(archived_items) == 1 and len(all_items) == 1
    assert await repository.duplicates(
        item.clinic_id, item.mobile_number, item.email, item.aadhaar_number, exclude_id=uuid4()
    ) == [item]
    assert await repository.duplicates(item.clinic_id, None, None, None) == []
    medical, dental = await repository.histories(item.id)
    assert medical is None and dental is None
    assert await repository.timeline(item.clinic_id, item.id) == [item]
    assert await repository.documents(item.clinic_id, item.id) == [item]
    assert await repository.get_document(item.clinic_id, item.id, item.id) is None

