from datetime import date, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.patient import Patient
from app.models.treatment import (
    Treatment,
    TreatmentStatus,
)
from app.schemas.treatment import (
    FollowUpCreate,
    ProcedureCreate,
    SOAPNotes,
    TreatmentCancel,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentUpdate,
)
from app.services.treatment_service import TreatmentService


class ScalarRows:
    def __init__(self, values):
        self.values = list(values) if values is not None else []

    def all(self):
        return self.values

    def first(self):
        return self.values[0] if self.values else None

    def scalars(self):
        return self

    def scalar_one(self):
        return self.values[0] if self.values else 0

    def scalar_one_or_none(self):
        return self.values[0] if self.values else None


class FakeDb:
    def __init__(self, items=None, active_treatment=None):
        self.items = items or []
        self.active_treatment = active_treatment
        self.added = []
        self.flushes = 0
        self.commits = 0

    def add(self, item):
        self.added.append(item)
        if isinstance(item, Treatment) and item not in self.items:
            self.items.append(item)

    async def flush(self):
        self.flushes += 1

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        pass

    async def get(self, model, id_):
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def scalar(self, query):
        return self.items[0] if self.items else None

    async def scalars(self, query):
        return ScalarRows(self.items)

    async def execute(self, query):
        text = str(query).lower()
        if "count(" in text:
            return ScalarRows([1])

        params = {}
        try:
            params = query.compile().params or {}
        except Exception:
            pass
        param_values = set(params.values())

        if "treatments" in text:
            treatments = [item for item in self.items if isinstance(item, Treatment)]

            # Check if querying by specific treatment id
            matching_by_id = [t for t in treatments if t.id in param_values]
            if matching_by_id:
                return ScalarRows(matching_by_id)

            # Check if querying active by appointment
            if "appointment_id" in text:
                if self.active_treatment:
                    return ScalarRows([self.active_treatment])
                matching_by_app = [
                    t for t in treatments
                    if getattr(t, "appointment_id", None) in param_values
                    and t.status != TreatmentStatus.CANCELLED
                    and getattr(t, "deleted_at", None) is None
                ]
                return ScalarRows(matching_by_app)

            # Check if querying by patient
            if "patient_id" in text:
                matching_by_pat = [t for t in treatments if getattr(t, "patient_id", None) in param_values]
                return ScalarRows(matching_by_pat)

            return ScalarRows(treatments)

        return ScalarRows(self.items)


def setup_fixtures(clinic_id=None):
    c_id = clinic_id or uuid4()
    patient = Patient(
        id=uuid4(),
        clinic_id=c_id,
        patient_number="PAT-001",
        first_name="Anita",
        last_name="Deshmukh",
        gender="FEMALE",
        date_of_birth=date(1988, 3, 14),
        mobile_number="9823456789",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=c_id,
        email="dr.ananya@test.com",
        password_hash="hash",
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
    )
    admin = User(
        id=uuid4(),
        clinic_id=c_id,
        email="admin@test.com",
        password_hash="hash",
        first_name="Admin",
        last_name="User",
        role=Role.CLINIC_ADMIN,
    )
    appointment = Appointment(
        id=uuid4(),
        clinic_id=c_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=uuid4(),
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
        start_time=datetime.strptime("11:00", "%H:%M").time(),
        end_time=datetime.strptime("11:45", "%H:%M").time(),
        duration=45,
        status=AppointmentStatus.CHECKED_IN,
        visit_type=VisitType.ROOT_CANAL,
    )
    appointment.patient = patient
    appointment.dentist = dentist
    return c_id, patient, dentist, admin, appointment


@pytest.mark.asyncio
async def test_treatment_service_create_success():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()
    db = FakeDb(items=[patient, dentist, appointment])
    service = TreatmentService(db)

    payload = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Class II mesio-occlusal cavity on #25",
        chief_complaint="Food lodgement between upper left premolars",
        clinical_findings="Proximal decay on distal of #24 and mesial of #25",
        treatment_plan="Composite restoration with sectional matrix",
        procedure_performed="Caries excavation, etching, bonding, composite curing",
        local_anaesthesia_used="Lignocaine 2% (0.9ml infiltration)",
        medicines_used="None required",
        clinical_notes="Margin well sealed, occlusion checked with articulating paper",
        soap=SOAPNotes(
            subjective="Food lodgement",
            objective="Cavitary defect distal #24",
            assessment="Class II dental caries",
            plan="Restore with nanohybrid composite",
        ),
        follow_up_instructions="Resume normal eating once numbness subsides",
        status=TreatmentStatus.IN_PROGRESS,
        procedures=[
            ProcedureCreate(
                procedure_name="Composite Restoration Class II",
                tooth_number="25",
                quantity=1,
                cost=2200.0,
                duration=35,
            )
        ],
        follow_up=FollowUpCreate(
            follow_up_date=date(2026, 9, 15),
            reason="Check contact point and polish",
        ),
    )

    detail = await service.create_treatment(clinic_id, payload, dentist)

    assert detail.diagnosis == payload.diagnosis
    assert detail.treatment_number.startswith("TRT-20260908-")
    assert appointment.status == AppointmentStatus.IN_TREATMENT
    assert appointment.start_datetime is not None
    assert db.commits >= 1


@pytest.mark.asyncio
async def test_treatment_service_create_validations():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()

    # 1. Patient not found
    db = FakeDb(items=[dentist, appointment])
    service = TreatmentService(db)
    payload = TreatmentCreate(
        patient_id=uuid4(),
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Caries",
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, payload, dentist)
    assert exc.value.status_code == 404
    assert "Patient not found" in exc.value.detail

    # 2. Appointment not found
    db = FakeDb(items=[patient, dentist])
    service = TreatmentService(db)
    payload_app_missing = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        diagnosis="Caries",
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, payload_app_missing, dentist)
    assert exc.value.status_code == 404
    assert "Appointment not found" in exc.value.detail

    # 3. Appointment belongs to another patient
    wrong_patient_app = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        dentist_id=dentist.id,
        chair_id=uuid4(),
        appointment_number="APT-999",
        date=date(2026, 9, 8),
        start_time=datetime.strptime("11:00", "%H:%M").time(),
        end_time=datetime.strptime("11:30", "%H:%M").time(),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
        visit_type=VisitType.CONSULTATION,
    )
    db = FakeDb(items=[patient, dentist, wrong_patient_app])
    service = TreatmentService(db)
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(
            clinic_id,
            TreatmentCreate(
                patient_id=patient.id,
                appointment_id=wrong_patient_app.id,
                dentist_id=dentist.id,
                diagnosis="Caries",
            ),
            dentist,
        )
    assert exc.value.status_code == 400
    assert "does not belong to this patient" in exc.value.detail

    # 4. Clinician not found
    db = FakeDb(items=[patient, appointment])
    service = TreatmentService(db)
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(
            clinic_id,
            TreatmentCreate(
                patient_id=patient.id,
                appointment_id=appointment.id,
                dentist_id=uuid4(),
                diagnosis="Caries",
            ),
            dentist,
        )
    assert exc.value.status_code == 404
    assert "Clinician not found" in exc.value.detail


@pytest.mark.asyncio
async def test_treatment_service_duplicate_active_treatment_rule():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()
    existing_trt = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Existing Caries",
        status=TreatmentStatus.IN_PROGRESS,
    )
    existing_trt.patient = patient
    existing_trt.dentist = dentist
    existing_trt.appointment = appointment
    existing_trt.procedures = []
    existing_trt.follow_ups = []

    db = FakeDb(items=[patient, dentist, admin, appointment, existing_trt], active_treatment=existing_trt)
    service = TreatmentService(db)

    # 1. Non-override attempt is rejected
    payload_no_override = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Second treatment without override",
        is_override=False,
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, payload_no_override, dentist)
    assert exc.value.status_code == 400
    assert "already exists for this appointment" in exc.value.detail

    # 2. Override attempt by regular DENTIST is forbidden (requires ADMIN)
    payload_override = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Second treatment with override by dentist",
        is_override=True,
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, payload_override, dentist)
    assert exc.value.status_code == 403
    assert "Only clinic administrators can override" in exc.value.detail

    # 3. Override by CLINIC_ADMIN is allowed
    # Set active_treatment=None on second call so it succeeds
    db.active_treatment = None
    detail = await service.create_treatment(clinic_id, payload_override, admin)
    assert detail is not None
    assert detail.is_override is True


@pytest.mark.asyncio
async def test_treatment_service_follow_up_date_validation():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()
    db = FakeDb(items=[patient, dentist, appointment])
    service = TreatmentService(db)

    # Follow-up date earlier than appointment date (2026-09-08)
    invalid_followup = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Gingivitis",
        follow_up=FollowUpCreate(
            follow_up_date=date(2026, 9, 7),  # yesterday!
            reason="Review",
        ),
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, invalid_followup, dentist)
    assert exc.value.status_code == 400
    assert "cannot be before the treatment date" in exc.value.detail


@pytest.mark.asyncio
async def test_treatment_service_update_and_completed_immutability():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Pulpitis",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[patient, dentist, appointment, treatment])
    service = TreatmentService(db)

    # 1. Update open treatment works
    updated = await service.update_treatment(
        clinic_id,
        treatment.id,
        TreatmentUpdate(diagnosis="Acute Irreversible Pulpitis"),
        dentist,
    )
    assert updated.diagnosis == "Acute Irreversible Pulpitis"

    # 2. Complete treatment
    completed = await service.complete_treatment(
        clinic_id,
        treatment.id,
        TreatmentComplete(notes="Finished all canals", complete_appointment=True),
        dentist,
    )
    assert completed.status == TreatmentStatus.COMPLETED
    assert appointment.status == AppointmentStatus.COMPLETED

    # 3. Attempting to update COMPLETED treatment raises 400 (Immutability rule)
    with pytest.raises(HTTPException) as exc:
        await service.update_treatment(
            clinic_id,
            treatment.id,
            TreatmentUpdate(diagnosis="Attempting change"),
            dentist,
        )
    assert exc.value.status_code == 400
    assert "permanently locked" in exc.value.detail

    # 4. Attempting to cancel COMPLETED treatment raises 400
    with pytest.raises(HTTPException) as exc:
        await service.cancel_treatment(
            clinic_id,
            treatment.id,
            TreatmentCancel(reason="Trying to cancel completed"),
            dentist,
        )
    assert exc.value.status_code == 400
    assert "cannot be cancelled" in exc.value.detail

    # 5. Attempting to delete COMPLETED treatment raises 400
    with pytest.raises(HTTPException) as exc:
        await service.delete_treatment(clinic_id, treatment.id, admin)
    assert exc.value.status_code == 400
    assert "cannot be deleted" in exc.value.detail


@pytest.mark.asyncio
async def test_treatment_service_cancel_and_delete_authorization():
    clinic_id, patient, dentist, admin, appointment = setup_fixtures()
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0002",
        diagnosis="Crown preparation",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[treatment])
    service = TreatmentService(db)

    # 1. Non-admin cannot delete
    with pytest.raises(HTTPException) as exc:
        await service.delete_treatment(clinic_id, treatment.id, dentist)
    assert exc.value.status_code == 403
    assert "Only clinic administrators can delete" in exc.value.detail

    # 2. Admin can delete
    res = await service.delete_treatment(clinic_id, treatment.id, admin)
    assert "deleted successfully" in res["detail"]
    assert treatment.deleted_at is not None
