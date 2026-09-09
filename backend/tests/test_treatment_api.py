from datetime import date, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import appointments as apt_api
from app.api.v1 import patients as pat_api
from app.api.v1 import treatments as trt_api
from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.patient import Patient
from app.models.treatment import Treatment, TreatmentStatus
from app.schemas.treatment import (
    ProcedureCreate,
    TreatmentCancel,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentUpdate,
)


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

    def add(self, item):
        self.added.append(item)
        if isinstance(item, Treatment) and item not in self.items:
            self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

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

        if "treatments" in text:
            treatments = [item for item in self.items if isinstance(item, Treatment)]

            # Check if querying by specific treatment id
            id_params = [v for k, v in params.items() if k.startswith("id_") or k == "id"]
            if id_params:
                matching = [t for t in treatments if t.id in id_params]
                return ScalarRows(matching)

            # Check if querying by appointment
            app_params = [v for k, v in params.items() if k.startswith("appointment_id")]
            if app_params:
                if self.active_treatment:
                    return ScalarRows([self.active_treatment])
                matching = [t for t in treatments if getattr(t, "appointment_id", None) in app_params]
                return ScalarRows(matching)

            # Check if querying by patient
            pat_params = [v for k, v in params.items() if k.startswith("patient_id")]
            if pat_params:
                matching = [t for t in treatments if getattr(t, "patient_id", None) in pat_params]
                return ScalarRows(matching)

            return ScalarRows(treatments)

        return ScalarRows(self.items)


def setup_api_fixtures():
    clinic_id = uuid4()
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-001",
        first_name="Ramesh",
        last_name="Gupta",
        gender="MALE",
        date_of_birth=date(1992, 7, 10),
        mobile_number="9812345678",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@test.com",
        password_hash="hash",
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
    )
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@test.com",
        password_hash="hash",
        first_name="Admin",
        last_name="User",
        role=Role.CLINIC_ADMIN,
    )
    appointment = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=uuid4(),
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
        start_time=datetime.strptime("09:30", "%H:%M").time(),
        end_time=datetime.strptime("10:15", "%H:%M").time(),
        duration=45,
        status=AppointmentStatus.CHECKED_IN,
        visit_type=VisitType.ROOT_CANAL,
    )
    appointment.patient = patient
    appointment.dentist = dentist

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Marginal periodontitis",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    return clinic_id, patient, dentist, admin, appointment, treatment


@pytest.mark.asyncio
async def test_treatment_api_create_and_read():
    clinic_id, patient, dentist, admin, appointment, treatment = setup_api_fixtures()
    db = FakeDb(items=[patient, dentist, appointment])

    payload = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Enamel fracture on #11",
        procedures=[
            ProcedureCreate(
                procedure_name="Composite veneering",
                tooth_number="11",
                quantity=1,
                cost=3500.0,
            )
        ],
    )

    detail = await trt_api.create_treatment(payload, actor=dentist, db=db)
    assert detail.diagnosis == "Enamel fracture on #11"
    assert detail.treatment_number.startswith("TRT-20260908-")

    # Read endpoint
    db.items.append(treatment)
    read_detail = await trt_api.get_treatment(treatment.id, actor=dentist, db=db)
    assert read_detail.id == treatment.id

    # List endpoint
    items = await trt_api.list_treatments(actor=dentist, db=db)
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_treatment_api_update_complete_cancel_delete():
    clinic_id, patient, dentist, admin, appointment, treatment = setup_api_fixtures()
    db = FakeDb(items=[patient, dentist, appointment, treatment])

    # 1. Update
    updated = await trt_api.update_treatment(
        treatment.id,
        TreatmentUpdate(diagnosis="Severe marginal periodontitis"),
        actor=dentist,
        db=db,
    )
    assert updated.diagnosis == "Severe marginal periodontitis"

    # 2. Complete
    completed = await trt_api.complete_treatment(
        treatment.id,
        TreatmentComplete(notes="Scaling and root planing completed"),
        actor=dentist,
        db=db,
    )
    assert completed.status == TreatmentStatus.COMPLETED

    # Reset status to IN_PROGRESS for cancel and delete tests
    treatment.status = TreatmentStatus.IN_PROGRESS

    # 3. Cancel
    cancelled = await trt_api.cancel_treatment(
        treatment.id,
        TreatmentCancel(reason="Patient unable to tolerate procedure"),
        actor=dentist,
        db=db,
    )
    assert cancelled.status == TreatmentStatus.CANCELLED

    # Reset for delete
    treatment.status = TreatmentStatus.IN_PROGRESS

    # 4. Delete
    res = await trt_api.delete_treatment(treatment.id, actor=admin, db=db)
    assert "deleted successfully" in res["detail"]


@pytest.mark.asyncio
async def test_treatment_api_patient_and_appointment_endpoints():
    clinic_id, patient, dentist, admin, appointment, treatment = setup_api_fixtures()
    db = FakeDb(items=[patient, dentist, appointment, treatment])

    # Route: GET /treatments/patient/{id}
    trt_list = await trt_api.list_patient_treatments(patient.id, actor=dentist, db=db)
    assert len(trt_list) >= 1

    # Route: GET /treatments/appointment/{id}
    app_trt = await trt_api.get_appointment_treatment(appointment.id, actor=dentist, db=db)
    assert app_trt is not None
    assert app_trt.id == treatment.id

    # Route alias: GET /patients/{id}/treatments
    pat_trt_list = await pat_api.list_patient_treatments_endpoint(patient.id, actor=dentist, db=db)
    assert len(pat_trt_list) >= 1

    # Route alias: GET /appointments/{id}/treatment
    app_alias_trt = await apt_api.get_appointment_treatment_endpoint(appointment.id, actor=dentist, db=db)
    assert app_alias_trt is not None
    assert app_alias_trt.id == treatment.id

    # Dashboard stats: GET /treatments/dashboard/stats
    stats = await trt_api.get_treatment_dashboard_stats(actor=dentist, db=db)
    assert stats.total_treatments >= 1


@pytest.mark.asyncio
async def test_treatment_api_clinic_context_required():
    clinic_id, patient, dentist, admin, appointment, treatment = setup_api_fixtures()
    no_clinic_user = User(
        id=uuid4(),
        clinic_id=None,
        email="super@test.com",
        password_hash="hash",
        first_name="Super",
        last_name="Admin",
        role=Role.SUPER_ADMIN,
    )
    db = FakeDb()

    with pytest.raises(HTTPException) as exc:
        await trt_api.create_treatment(
            TreatmentCreate(patient_id=patient.id, appointment_id=appointment.id, dentist_id=dentist.id, diagnosis="X"),
            actor=no_clinic_user,
            db=db,
        )
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException):
        await trt_api.list_treatments(actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.get_treatment(treatment.id, actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.update_treatment(treatment.id, TreatmentUpdate(diagnosis="Y"), actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.complete_treatment(treatment.id, TreatmentComplete(), actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.cancel_treatment(treatment.id, TreatmentCancel(reason="None"), actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.delete_treatment(treatment.id, actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.list_patient_treatments(patient.id, actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.get_appointment_treatment(appointment.id, actor=no_clinic_user, db=db)

    with pytest.raises(HTTPException):
        await trt_api.get_treatment_dashboard_stats(actor=no_clinic_user, db=db)
