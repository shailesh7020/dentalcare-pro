from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    AppointmentTimelineEvent,
    Chair,
    ChairStatus,
    VisitType,
)
from app.models.identity import AuditEvent, Clinic, Role, User
from app.models.patient import PatientTimelineEvent
from app.models.treatment import (
    Treatment,
    TreatmentFollowUp,
    TreatmentProcedure,
    TreatmentStatus,
)
from app.schemas.appointment import AppointmentCreate
from app.schemas.patient import MedicalHistoryInput, PatientInput
from app.schemas.treatment import (
    FollowUpCreate,
    ProcedureCreate,
    SOAPNotes,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentUpdate,
)
from app.security.passwords import hash_password
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService
from app.services.treatment_service import TreatmentService


class E2ESession:
    def __init__(self) -> None:
        self.entities: list[object] = []
        self.added: list[object] = []
        self.commits = 0

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.entities:
            self.entities.append(item)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model_cls: type, ident: UUID | str) -> object | None:
        for item in self.entities:
            if isinstance(item, model_cls) and getattr(item, "id", None) == ident:
                return item
        return None

    def _filter_by_query(self, statement: object) -> list[object]:
        params: dict[str, object] = {}
        try:
            params = statement.compile().params or {}  # type: ignore[attr-defined]
        except Exception:
            pass

        matching = list(self.entities)
        if hasattr(statement, "column_descriptions") and statement.column_descriptions:
            desc = statement.column_descriptions[0]
            entity_cls = desc.get("entity")
            if isinstance(entity_cls, type):
                matching = [item for item in matching if isinstance(item, entity_cls)]

        clinic_ids = [v for k, v in params.items() if "clinic_id" in k]
        id_values = [v for k, v in params.items() if k == "id" or k.startswith("id_")]

        if clinic_ids:
            matching = [item for item in matching if getattr(item, "clinic_id", None) in clinic_ids]
        if id_values:
            matching = [item for item in matching if getattr(item, "id", None) in id_values]
        return matching

    async def scalar(self, statement: object) -> object | None:
        matching = self._filter_by_query(statement)
        return matching[0] if matching else None

    async def scalars(self, statement: object) -> SimpleNamespace:
        matching = self._filter_by_query(statement)
        return SimpleNamespace(all=lambda: list(matching))

    async def execute(self, statement: object) -> SimpleNamespace:
        text = str(statement).lower()
        if "count(" in text:
            return SimpleNamespace(
                scalar_one=lambda: 0,
                scalar_one_or_none=lambda: 0,
                scalars=lambda: SimpleNamespace(all=lambda: [0]),
            )
        matching = self._filter_by_query(statement)
        return SimpleNamespace(
            scalar_one_or_none=lambda: matching[0] if matching else None,
            scalar_one=lambda: len(matching),
            scalars=lambda: SimpleNamespace(
                all=lambda: list(matching),
                first=lambda: matching[0] if matching else None,
            ),
        )


@pytest.mark.asyncio
async def test_full_clinical_lifecycle_e2e() -> None:
    """
    End-to-End Clinical Lifecycle Verification Test:
    1. Clinic Setup: Admin, Dentist, Receptionist, Dental Chair
    2. Patient Intake: Receptionist registers patient with medical history
    3. Scheduling: Receptionist books appointment
    4. Check-In: Patient arrives, appointment marked CHECKED_IN
    5. Treatment Start: Dentist starts treatment, appointment transitions to IN_TREATMENT
    6. Clinical Notes: Procedures recorded, SOAP notes documented
    7. Completion: Treatment completed, record locked (immutable), appointment completed
    8. Longitudinal Verification: Timelines and audit trails validated
    """
    db = E2ESession()
    clinic_id = uuid4()

    # ------------------------------------------------------------------------
    # Step 1: Staff & Clinic Setup
    # ------------------------------------------------------------------------
    clinic = Clinic(
        id=clinic_id,
        name="Apex Dental Care",
        slug="apex-dental",
        email="info@apexdental.com",
        phone="9876540000",
        timezone="Asia/Kolkata",
        is_active=True,
    )
    db.add(clinic)

    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@apexdental.com",
        password_hash=hash_password("AdminSecure2026!"),
        first_name="Anita",
        last_name="Deshmukh",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )
    db.add(admin)

    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@apexdental.com",
        password_hash=hash_password("DentistSecure2026!"),
        first_name="Vikram",
        last_name="Malhotra",
        role=Role.DENTIST,
        is_active=True,
    )
    db.add(dentist)

    receptionist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="reception@apexdental.com",
        password_hash=hash_password("ReceptionSecure2026!"),
        first_name="Pooja",
        last_name="Sharma",
        role=Role.RECEPTIONIST,
        is_active=True,
    )
    db.add(receptionist)

    chair = Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Operatory Chair 1",
        room_number="Room 101",
        status=ChairStatus.ACTIVE,
        is_active=True,
    )
    db.add(chair)

    # ------------------------------------------------------------------------
    # Step 2: Patient Intake (Receptionist registers patient)
    # ------------------------------------------------------------------------
    patient_service = PatientService(db, actor=receptionist)  # type: ignore[arg-type]

    patient_payload = PatientInput(
        first_name="Sunil",
        last_name="Verma",
        gender="MALE",
        date_of_birth=date(1988, 6, 15),
        blood_group="B+",
        mobile_number="9876512345",
        email="sunil.verma@example.com",
        city="Pune",
        state="Maharashtra",
        country="India",
        pin_code="411001",
        emergency_contact_name="Meera Verma",
        emergency_contact_number="9876512346",
        emergency_contact_relation="Spouse",
        medical_history=MedicalHistoryInput(
            diabetes=False,
            hypertension=True,
            allergies="Penicillin",
            current_medications="Amlodipine 5mg",
        ),
    )

    patient, _ = await patient_service.create(patient_payload)
    assert patient.id is not None
    assert patient.patient_number.startswith("P-")
    assert patient.first_name == "Sunil"
    assert patient.clinic_id == clinic_id
    db.add(patient)

    # Verify patient timeline event created
    timeline_events = [e for e in db.added if isinstance(e, PatientTimelineEvent)]
    assert len(timeline_events) >= 1
    assert any(e.event_type == "PATIENT_CREATED" for e in timeline_events)

    # ------------------------------------------------------------------------
    # Step 3: Appointment Scheduling (Receptionist books appointment)
    # ------------------------------------------------------------------------
    apt_service = AppointmentService(db)  # type: ignore[arg-type]

    target_appointment_date = datetime.now(UTC).date() + timedelta(days=1)
    apt_payload = AppointmentCreate(
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        date=target_appointment_date,
        start_time=time(10, 0),
        duration=45,
        visit_type=VisitType.CONSULTATION,
        chief_complaint="Severe pain in upper right premolar",
    )

    appointment = await apt_service.create(clinic_id, apt_payload, receptionist)
    assert appointment.id is not None
    assert appointment.status == AppointmentStatus.SCHEDULED
    assert appointment.patient_id == patient.id
    assert appointment.dentist_id == dentist.id
    assert appointment.chair_id == chair.id

    # Retrieve real appointment entity and link relations for in-memory model
    apt_entity = await db.get(Appointment, appointment.id)
    assert apt_entity is not None
    apt_entity.patient = patient
    apt_entity.dentist = dentist
    apt_entity.chair = chair
    apt_entity.timeline_events = [e for e in db.added if isinstance(e, AppointmentTimelineEvent)]
    db.add(apt_entity)

    # ------------------------------------------------------------------------
    # Step 4: Patient Arrival & Check-In
    # ------------------------------------------------------------------------
    updated_apt = await apt_service.checkin(
        clinic_id=clinic_id,
        appointment_id=appointment.id,
        actor=receptionist,
    )
    assert updated_apt.status == AppointmentStatus.CHECKED_IN

    # ------------------------------------------------------------------------
    # Step 5: Dentist Starts Treatment
    # ------------------------------------------------------------------------
    treatment_service = TreatmentService(db)  # type: ignore[arg-type]

    treatment_payload = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Irreversible Pulpitis tooth #14",
        chief_complaint="Severe spontaneous throbbing pain radiating to ear",
        clinical_findings="Deep carious lesion on mesio-occlusal surface of tooth #14, tender on percussion",
        treatment_plan="Root canal treatment and porcelain crown",
        local_anaesthesia_used="2% Lignocaine with 1:80000 Adrenaline (1.8ml)",
        soap=SOAPNotes(
            subjective="Patient reports acute throbbing pain keeping him awake at night.",
            objective="Deep carious lesion #14. Pulp sensitivity test positive (lingering pain).",
            assessment="Irreversible pulpitis #14 without periapical lesion.",
            plan="Access opening, biomechanical preparation, temporary dressing, recall for obturation.",
        ),
        procedures=[
            ProcedureCreate(
                procedure_name="Root Canal Treatment (Multi-Rooted)",
                tooth_number="14",
                quantity=1,
                cost=4500.00,
                duration=45,
                notes="Access cavity made, pulp extirpated, canals shaped to F2 Protaper.",
            ),
        ],
        follow_up=FollowUpCreate(
            follow_up_date=target_appointment_date + timedelta(days=5),
            reason="Canal Obturation & Temporary Restoration Check",
            instructions="Maintain soft diet on right side. Contact clinic if pain persists.",
        ),
    )

    treatment = await treatment_service.create_treatment(
        clinic_id=clinic_id,
        payload=treatment_payload,
        actor=dentist,
    )
    assert treatment.id is not None
    assert treatment.treatment_number.startswith("TRT-")
    assert treatment.status == TreatmentStatus.IN_PROGRESS
    assert len(treatment.procedures) == 1
    assert len(treatment.follow_ups) == 1
    assert treatment.follow_ups[0].reason == "Canal Obturation & Temporary Restoration Check"

    # Verify Appointment automatically synchronized to IN_TREATMENT
    apt_entity = await db.get(Appointment, appointment.id)
    assert apt_entity.status == AppointmentStatus.IN_TREATMENT
    assert apt_entity.start_datetime is not None

    # Link treatment relations for in-memory detail views
    treatment_entity = await db.get(Treatment, treatment.id)
    assert treatment_entity is not None
    treatment_entity.patient = patient
    treatment_entity.dentist = dentist
    treatment_entity.appointment = apt_entity
    treatment_entity.procedures = [p for p in db.added if isinstance(p, TreatmentProcedure)]
    treatment_entity.follow_ups = [f for f in db.added if isinstance(f, TreatmentFollowUp)]
    apt_entity.treatment = treatment_entity
    db.add(treatment_entity)

    # ------------------------------------------------------------------------
    # Step 6: Clinical Documentation & Procedures Update
    # ------------------------------------------------------------------------
    treatment_update_payload = TreatmentUpdate(
        clinical_notes="Canals irrigated thoroughly with 3% NaOCl and saline. Calcium hydroxide placed.",
    )
    updated_treatment = await treatment_service.update_treatment(
        clinic_id=clinic_id,
        treatment_id=treatment.id,
        payload=treatment_update_payload,
        actor=dentist,
    )
    assert "Calcium hydroxide placed" in (updated_treatment.clinical_notes or "")

    # ------------------------------------------------------------------------
    # Step 7: Dentist Completes Treatment & Visit
    # ------------------------------------------------------------------------
    completion_payload = TreatmentComplete(
        notes="First sitting of RCT successfully finished without complications.",
        complete_appointment=True,
    )
    completed_treatment = await treatment_service.complete_treatment(
        clinic_id=clinic_id,
        treatment_id=treatment.id,
        payload=completion_payload,
        actor=dentist,
    )
    assert completed_treatment.status == TreatmentStatus.COMPLETED
    assert completed_treatment.completed_at is not None

    # Verify linked appointment is also COMPLETED
    assert apt_entity.status == AppointmentStatus.COMPLETED
    assert apt_entity.end_datetime is not None

    # ------------------------------------------------------------------------
    # Step 8: Immutability Enforcement on Completed Medical Record
    # ------------------------------------------------------------------------
    with pytest.raises(HTTPException) as exc:
        await treatment_service.update_treatment(
            clinic_id=clinic_id,
            treatment_id=treatment.id,
            payload=TreatmentUpdate(clinical_findings="Malicious retrospective edit"),
            actor=dentist,
        )
    assert exc.value.status_code == 400
    assert "permanently locked and cannot be edited" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        await treatment_service.delete_treatment(
            clinic_id=clinic_id,
            treatment_id=treatment.id,
            actor=admin,
        )
    assert exc.value.status_code == 400
    assert "Completed treatments cannot be deleted" in exc.value.detail

    # ------------------------------------------------------------------------
    # Step 9: Audit Trail & Timeline Integrity Verification
    # ------------------------------------------------------------------------
    all_audit_events = [e for e in db.added if isinstance(e, AuditEvent)]
    assert len(all_audit_events) >= 3

    all_timeline_events = [e for e in db.added if isinstance(e, PatientTimelineEvent)]
    assert len(all_timeline_events) >= 2
    timeline_types = [e.event_type for e in all_timeline_events]
    assert "PATIENT_CREATED" in timeline_types
    assert "TREATMENT_CREATED" in timeline_types or "TREATMENT_UPDATED" in timeline_types
