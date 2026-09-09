from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.odontogram import Tooth, ToothCondition, ToothSurface
from app.models.patient import Patient, PatientTimelineEvent
from app.models.treatment import Treatment
from app.schemas.treatment import (
    ProcedureCreate,
    SOAPNotes,
    TreatmentCreate,
)
from app.services.odontogram_service import OdontogramService
from app.services.treatment_service import TreatmentService


class InMemorySyncDb:
    def __init__(self, patient: Patient, dentist: User, appointment: Appointment):
        self.patient = patient
        self.dentist = dentist
        self.appointment = appointment
        self.items: list[object] = [patient, dentist, appointment]
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, statement: object) -> object:
        text = str(statement).lower()
        from types import SimpleNamespace

        if "count(" in text:
            return SimpleNamespace(
                scalar_one=lambda: 0,
                scalar_one_or_none=lambda: 0,
                scalars=lambda: SimpleNamespace(all=lambda: [0]),
            )

        matching = list(self.items)
        if "tooth_surfaces" in text:
            matching = [item for item in self.items if isinstance(item, ToothSurface)]
        elif "teeth" in text:
            matching = [item for item in self.items if isinstance(item, Tooth)]
        elif "treatments" in text:
            matching = [item for item in self.items if isinstance(item, Treatment)]
        elif "appointments" in text:
            matching = [item for item in self.items if isinstance(item, Appointment)]

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: list(matching),
                first=lambda: matching[0] if matching else None,
            ),
            scalar_one_or_none=lambda: matching[0] if matching else None,
        )


@pytest.mark.asyncio
async def test_treatment_sync_updates_odontogram():
    clinic_id = uuid4()
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-SYNC-01",
        first_name="Kavita",
        last_name="Rao",
        gender="FEMALE",
        mobile_number="9876543210",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.rao@clinic.com",
        first_name="Anand",
        last_name="Rao",
        role=Role.DENTIST,
    )
    appointment = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        date=date(2026, 9, 10),
        status=AppointmentStatus.CHECKED_IN,
        visit_type=VisitType.ROOT_CANAL,
        appointment_number="APT-20260910-0001",
    )

    db = InMemorySyncDb(patient, dentist, appointment)
    odontogram_service = OdontogramService(db)  # type: ignore[arg-type]

    # Initialize odontogram
    await odontogram_service.get_patient_odontogram(clinic_id, patient.id, "ADULT", dentist.id)

    # Verify tooth #14 is initially healthy
    t14 = await odontogram_service.repo.get_tooth_by_number(clinic_id, patient.id, "14")
    assert t14 is not None
    assert t14.primary_status == ToothCondition.HEALTHY.value

    # Create treatment with Root Canal on tooth #14
    treatment_service = TreatmentService(db)  # type: ignore[arg-type]
    treatment_payload = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Irreversible Pulpitis tooth #14",
        procedures=[
            ProcedureCreate(
                procedure_name="Root Canal Treatment (Multi-Rooted)",
                tooth_number="14",
                quantity=1,
                cost=4500.0,
                duration=45,
            )
        ],
        soap=SOAPNotes(
            subjective="Severe toothache",
            objective="Decay on #14",
            assessment="Pulpitis",
            plan="Endodontic therapy",
        ),
    )

    treatment = await treatment_service.create_treatment(clinic_id, treatment_payload, dentist)
    assert treatment.id is not None

    # Verify tooth #14 has been automatically updated in the odontogram!
    assert t14.has_root_canal is True
    assert t14.primary_status == ToothCondition.ROOT_CANAL.value
    assert t14.color == "#8B5CF6"

    # Verify patient timeline event was created for odontogram sync
    timeline_events = [e for e in db.added if isinstance(e, PatientTimelineEvent)]
    assert any(e.event_type == "ODONTOGRAM_UPDATED" for e in timeline_events)
