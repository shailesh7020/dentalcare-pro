from datetime import date, datetime
from uuid import uuid4

import pytest

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.models.patient import MedicalHistory, Patient
from app.models.treatment import (
    Treatment,
    TreatmentStatus,
)
from app.repositories.treatment_repository import TreatmentRepository
from app.schemas.treatment import (
    FollowUpCreate,
    ProcedureCreate,
    SOAPNotes,
    TreatmentCreate,
    TreatmentUpdate,
)


class ScalarRows:
    def __init__(self, values):
        self.values = values

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
    def __init__(self, items=None, scalar_return=None):
        self.items = items or []
        self.scalar_return = scalar_return
        self.added = []
        self.flushes = 0
        self.commits = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushes += 1

    async def commit(self):
        self.commits += 1

    async def refresh(self, item):
        pass

    async def scalar(self, query):
        if self.scalar_return is not None:
            return self.scalar_return
        return self.items[0] if self.items else None

    async def scalars(self, query):
        return ScalarRows(self.items)

    async def get(self, model, id_):
        for item in self.items:
            if getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, query):
        if self.scalar_return is not None:
            return ScalarRows([self.scalar_return])
        return ScalarRows(self.items)


def sample_patient(clinic_id):
    p = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-001",
        first_name="Rohan",
        last_name="Verma",
        gender="MALE",
        date_of_birth=date(1990, 5, 20),
        mobile_number="9876543210",
    )
    p.medical_history = MedicalHistory(
        patient_id=p.id,
        cardiac_disease=True,
        hypertension=True,
        diabetes=False,
        allergies="Penicillin",
    )
    return p


def sample_dentist(clinic_id):
    return User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@test.com",
        password_hash="hash",
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
    )


def sample_appointment(clinic_id, patient_id, dentist_id):
    return Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        chair_id=uuid4(),
        appointment_number="APT-20260908-0001",
        date=date(2026, 9, 8),
        start_time=datetime.strptime("10:00", "%H:%M").time(),
        end_time=datetime.strptime("10:45", "%H:%M").time(),
        duration=45,
        status=AppointmentStatus.IN_TREATMENT,
        visit_type=VisitType.ROOT_CANAL,
    )


@pytest.mark.asyncio
async def test_treatment_repository_create_and_read():
    clinic_id = uuid4()
    patient = sample_patient(clinic_id)
    dentist = sample_dentist(clinic_id)
    appointment = sample_appointment(clinic_id, patient.id, dentist.id)

    db = FakeDb()
    repo = TreatmentRepository(db)

    payload = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        diagnosis="Deep dentinal caries on #46",
        chief_complaint="Severe pain when chewing",
        clinical_findings="Cavitation extending to pulpal wall",
        treatment_plan="Root canal therapy followed by porcelain crown",
        procedure_performed="Access cavity preparation and pulp extirpation",
        local_anaesthesia_used="Lignocaine 2% with adrenaline 1:80000 (1.8ml)",
        medicines_used="Amoxicillin 500mg TDS, Ibuprofen 400mg BD",
        clinical_notes="Procedure uneventful, canal irrigated with NaOCl",
        soap=SOAPNotes(
            subjective="Patient reports lingering pain",
            objective="Percussion positive on #46",
            assessment="Irreversible pulpitis",
            plan="Initiate RCT stage 1",
        ),
        follow_up_instructions="Avoid chewing on right side until temporary cement sets",
        status=TreatmentStatus.IN_PROGRESS,
        procedures=[
            ProcedureCreate(
                procedure_name="Root Canal Stage 1",
                tooth_number="46",
                quantity=1,
                cost=4500.0,
                duration=45,
                notes="Canals located: MB, ML, D",
            )
        ],
        follow_up=FollowUpCreate(
            follow_up_date=date(2026, 9, 15),
            reason="RCT Stage 2 - Canal shaping and obturation",
            instructions="Take prescribed medications",
        ),
    )

    treatment = await repo.create(clinic_id, payload, "TRT-20260908-0001", dentist.id)

    assert treatment.treatment_number == "TRT-20260908-0001"
    assert treatment.diagnosis == "Deep dentinal caries on #46"
    assert len(treatment.procedures) == 1
    assert treatment.procedures[0].tooth_number == "46"
    assert len(treatment.follow_ups) == 1
    assert treatment.follow_ups[0].follow_up_date == date(2026, 9, 15)
    assert db.flushes == 1

    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment

    read_model = repo.to_read_model(treatment)
    assert read_model.treatment_number == "TRT-20260908-0001"
    assert read_model.patient_name == "Rohan Verma"
    assert read_model.total_cost == 4500.0
    assert read_model.procedures_count == 1

    detail_model = repo.to_detail_model(treatment)
    assert "Cardiac Disease" in detail_model.patient_medical_alerts
    assert any("Penicillin" in a for a in detail_model.patient_medical_alerts)
    assert detail_model.soap_subjective == "Patient reports lingering pain"
    assert len(detail_model.procedures) == 1
    assert len(detail_model.follow_ups) == 1


@pytest.mark.asyncio
async def test_treatment_repository_update_and_complete():
    clinic_id = uuid4()
    patient = sample_patient(clinic_id)
    dentist = sample_dentist(clinic_id)
    appointment = sample_appointment(clinic_id, patient.id, dentist.id)

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Caries",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[treatment])
    repo = TreatmentRepository(db)

    update_payload = TreatmentUpdate(
        clinical_findings="Updated findings: clean margin",
        soap=SOAPNotes(assessment="Restoration stable"),
        procedures=[
            ProcedureCreate(
                procedure_name="Composite Restoration",
                tooth_number="46",
                quantity=1,
                cost=1500.0,
            )
        ],
    )

    updated = await repo.update(treatment, update_payload, dentist.id)
    assert updated.clinical_findings == "Updated findings: clean margin"
    assert updated.soap_assessment == "Restoration stable"
    assert len(updated.procedures) == 1
    assert updated.procedures[0].cost == 1500.0

    completed = await repo.complete(treatment, notes="All goals achieved", user_id=dentist.id)
    assert completed.status == TreatmentStatus.COMPLETED
    assert completed.completed_at is not None
    assert "[Completion Note]: All goals achieved" in (completed.clinical_notes or "")


@pytest.mark.asyncio
async def test_treatment_repository_cancel_and_delete():
    clinic_id = uuid4()
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        appointment_id=uuid4(),
        dentist_id=uuid4(),
        treatment_number="TRT-20260908-0002",
        diagnosis="Gingivitis",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[treatment])
    repo = TreatmentRepository(db)

    cancelled = await repo.cancel(treatment, reason="Patient requested to defer", user_id=uuid4())
    assert cancelled.status == TreatmentStatus.CANCELLED
    assert cancelled.cancellation_reason == "Patient requested to defer"

    deleted = await repo.soft_delete(treatment, user_id=uuid4())
    assert deleted.deleted_at is not None


@pytest.mark.asyncio
async def test_treatment_repository_generate_number_and_stats():
    clinic_id = uuid4()
    db = FakeDb(scalar_return=3)
    repo = TreatmentRepository(db)

    num = await repo.generate_treatment_number(clinic_id, target_date=date(2026, 9, 8))
    assert num == "TRT-20260908-0004"

    stats = await repo.get_dashboard_stats(clinic_id)
    assert stats.planned == 3
    assert stats.in_progress == 3
    assert stats.completed == 3
    assert stats.follow_ups_due == 3
    assert stats.total_treatments == 3


@pytest.mark.asyncio
async def test_treatment_repository_list_and_alerts():
    clinic_id = uuid4()
    patient = sample_patient(clinic_id)
    patient.medical_history.diabetes = True
    patient.medical_history.pregnancy = True
    patient.medical_history.infectious_diseases = "Hepatitis B"

    dentist = sample_dentist(clinic_id)
    appointment = sample_appointment(clinic_id, patient.id, dentist.id)

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0005",
        diagnosis="Caries",
        status=TreatmentStatus.PLANNED,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[treatment])
    repo = TreatmentRepository(db)

    # Test detail alerts
    detail = repo.to_detail_model(treatment)
    assert "Diabetes" in detail.patient_medical_alerts
    assert "Pregnancy" in detail.patient_medical_alerts
    assert any("Hepatitis B" in a for a in detail.patient_medical_alerts)

    # Test list_treatments with various filters
    list1 = await repo.list_treatments(
        clinic_id,
        search="Rohan",
        status=TreatmentStatus.PLANNED,
        dentist_id=dentist.id,
        patient_id=patient.id,
        target_date=date(2026, 9, 8),
    )
    assert len(list1) == 1

    list2 = await repo.list_treatments(
        clinic_id,
        status="PLANNED",
    )
    assert len(list2) == 1

    # Test get_by_appointment
    by_app = await repo.get_by_appointment(clinic_id, appointment.id)
    assert by_app is not None


@pytest.mark.asyncio
async def test_treatment_repository_update_all_fields():
    clinic_id = uuid4()
    patient = sample_patient(clinic_id)
    dentist = sample_dentist(clinic_id)
    appointment = sample_appointment(clinic_id, patient.id, dentist.id)

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0006",
        diagnosis="Initial",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment.patient = patient
    treatment.dentist = dentist
    treatment.appointment = appointment
    treatment.procedures = []
    treatment.follow_ups = []

    db = FakeDb(items=[treatment])
    repo = TreatmentRepository(db)

    update_payload = TreatmentUpdate(
        diagnosis="Updated Diagnosis",
        chief_complaint="New complaint",
        treatment_plan="New plan",
        procedure_performed="New proc performed",
        local_anaesthesia_used="Ligno 2%",
        medicines_used="Amox",
        clinical_notes="Notes here",
        follow_up_instructions="Care instructions",
        status=TreatmentStatus.IN_PROGRESS,
        soap=SOAPNotes(
            subjective="Subj",
            objective="Obj",
            assessment="Assess",
            plan="Plan",
        ),
        follow_up=FollowUpCreate(
            follow_up_date=date(2026, 9, 20),
            reason="Checkup",
        ),
    )

    updated = await repo.update(treatment, update_payload, dentist.id)
    assert updated.chief_complaint == "New complaint"
    assert updated.treatment_plan == "New plan"
    assert updated.procedure_performed == "New proc performed"
    assert updated.local_anaesthesia_used == "Ligno 2%"
    assert updated.medicines_used == "Amox"
    assert updated.clinical_notes == "Notes here"
    assert updated.follow_up_instructions == "Care instructions"
    assert len(updated.follow_ups) == 1
