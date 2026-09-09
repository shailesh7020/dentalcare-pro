from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus, VisitType
from app.models.billing import Invoice, InvoiceStatus
from app.models.identity import Clinic, Role, User
from app.models.odontogram import Tooth
from app.models.patient import Patient, PatientDocument
from app.models.prescription import Prescription, PrescriptionItem
from app.models.treatment import Treatment
from app.schemas.portal import (
    PortalAppointmentBookRequest,
    PortalAppointmentCancelRequest,
    PortalProfileUpdate,
    PortalRegisterRequest,
)
from app.services.patient_portal_service import PatientPortalService


class FakePortalDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        for it in self.added:
            if getattr(it, "id", None) is None:
                it.id = uuid4()
            if getattr(it, "created_at", None) is None:
                it.created_at = datetime.now(UTC)
            if getattr(it, "updated_at", None) is None:
                it.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for it in self.items:
            if isinstance(it, model) and getattr(it, "id", None) == id_:
                return it
        return None

    async def scalar(self, stmt: object) -> object:
        res = await self.execute(stmt)
        if hasattr(res, "scalar_one_or_none"):
            return res.scalar_one_or_none()
        return None

    async def execute(self, stmt: object) -> object:
        text = str(stmt).lower()
        from types import SimpleNamespace

        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic)]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: pats[0] if pats else None,
                scalars=lambda: SimpleNamespace(all=lambda: pats),
            )

        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User)]
            params = getattr(getattr(stmt, "compile", lambda: None)(), "params", {}) or {}
            param_vals = {str(v).lower() for v in params.values() if v is not None}
            if "where users.email =" in text:
                for u in users:
                    if u.email and (u.email.lower() in text or u.email.lower() in param_vals):
                        return SimpleNamespace(scalar_one_or_none=lambda u=u: u)
                return SimpleNamespace(scalar_one_or_none=lambda: None)
            if "where users.patient_id =" in text:
                for u in users:
                    if u.patient_id and (str(u.patient_id).lower() in text or str(u.patient_id).lower() in param_vals):
                        return SimpleNamespace(scalar_one_or_none=lambda u=u: u)
                return SimpleNamespace(scalar_one_or_none=lambda: None)
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        if "from appointments" in text:
            appts = [i for i in self.items if isinstance(i, Appointment) and i.deleted_at is None]
            if "count(" in text:
                return SimpleNamespace(scalar_one_or_none=lambda: len(appts))
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: appts),
                scalar_one_or_none=lambda: appts[0] if appts else None,
            )

        if "from prescriptions" in text:
            rxs = [i for i in self.items if isinstance(i, Prescription) and i.deleted_at is None]
            if "count(" in text:
                return SimpleNamespace(scalar_one_or_none=lambda: len(rxs))
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: rxs),
                scalar_one_or_none=lambda: rxs[0] if rxs else None,
            )

        if "from invoices" in text:
            invs = [i for i in self.items if isinstance(i, Invoice) and i.deleted_at is None]
            if "sum(" in text:
                total_due = sum(float(i.balance_due) for i in invs)
                return SimpleNamespace(scalar_one_or_none=lambda: total_due)
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: invs),
                scalar_one_or_none=lambda: invs[0] if invs else None,
            )

        if "from treatments" in text:
            ts = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: ts),
                scalar_one_or_none=lambda: ts[0] if ts else None,
            )

        if "from patient_documents" in text:
            docs = [i for i in self.items if isinstance(i, PatientDocument) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: docs),
                scalar_one_or_none=lambda: docs[0] if docs else None,
            )

        if "from teeth" in text:
            teeth = [i for i in self.items if isinstance(i, Tooth) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: teeth),
                scalar_one_or_none=lambda: teeth[0] if teeth else None,
            )

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=list),
            scalar_one_or_none=lambda: None,
        )


@pytest.fixture
def portal_setup():
    clinic_id = uuid4()
    clinic = Clinic(id=clinic_id, name="City Dental Care", slug="city-dental", is_active=True)
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@citydental.com",
        first_name="David",
        last_name="Tennant",
        role=Role.DENTIST,
        is_active=True,
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        first_name="Donna",
        last_name="Noble",
        patient_number="P-4401",
        mobile_number="+919911223344",
        email="donna.noble@tardis.com",
    )
    return clinic, dentist, patient


@pytest.mark.asyncio
async def test_patient_portal_registration_and_login(portal_setup):
    clinic, dentist, patient = portal_setup
    db = FakePortalDb([clinic, dentist, patient])
    portal_svc = PatientPortalService(db)

    # 1. Register portal user
    reg_payload = PortalRegisterRequest(
        clinic_slug=clinic.slug,
        patient_number=patient.patient_number,
        email="donna.noble@tardis.com",
        password="securePassword123!",
        first_name="Donna",
        last_name="Noble",
        mobile_number=patient.mobile_number,
    )
    tokens = await portal_svc.register_patient_account(reg_payload)
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None

    # 2. Authenticate
    auth_tokens, user = await portal_svc.authenticate_portal_user(
        "donna.noble@tardis.com", "securePassword123!"
    )
    assert auth_tokens.access_token is not None
    assert user.role == Role.PATIENT
    assert user.patient_id == patient.id


@pytest.mark.asyncio
async def test_portal_registration_validation(portal_setup):
    clinic, dentist, patient = portal_setup
    db = FakePortalDb([clinic, dentist, patient])
    portal_svc = PatientPortalService(db)

    # Mobile mismatch failure
    reg_payload = PortalRegisterRequest(
        clinic_slug=clinic.slug,
        patient_number=patient.patient_number,
        email="fake@tardis.com",
        password="securePassword123!",
        first_name="Donna",
        last_name="Noble",
        mobile_number="+910000000000",
    )
    with pytest.raises(HTTPException) as exc:
        await portal_svc.register_patient_account(reg_payload)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_portal_dashboard_summary(portal_setup):
    clinic, dentist, patient = portal_setup
    appt = Appointment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=uuid4(),
        appointment_number="APT-2026-0099",
        date=date(2026, 10, 15),
        start_time=time(14, 0),
        end_time=time(14, 45),
        duration=45,
        status=AppointmentStatus.CONFIRMED,
        visit_type=VisitType.CONSULTATION,
    )
    appt.dentist = dentist

    inv = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        invoice_number="INV-2026-01",
        date=date(2026, 9, 1),
        subtotal=500.0,
        discount_amount=50.0,
        tax_amount=22.5,
        grand_total=472.5,
        amount_paid=200.0,
        balance_due=272.5,
        status=InvoiceStatus.PARTIALLY_PAID,
        created_by=dentist.id,
        updated_by=dentist.id,
    )

    db = FakePortalDb([clinic, dentist, patient, appt, inv])
    portal_svc = PatientPortalService(db)

    summary = await portal_svc.get_dashboard_summary(patient.id, clinic.id)
    assert summary.patient_id == patient.id
    assert summary.clinic_name == clinic.name
    assert summary.next_appointment is not None
    assert summary.next_appointment["appointment_number"] == "APT-2026-0099"
    assert summary.total_balance_due == 272.5


@pytest.mark.asyncio
async def test_portal_appointment_booking_and_cancellation(portal_setup):
    clinic, dentist, patient = portal_setup
    db = FakePortalDb([clinic, dentist, patient])
    portal_svc = PatientPortalService(db)

    # Book
    book_req = PortalAppointmentBookRequest(
        dentist_id=dentist.id,
        appointment_date=date(2026, 11, 20),
        start_time=time(11, 0),
        visit_type=VisitType.CONSULTATION,
        reason="Routine cleaning and scaling checkup",
    )
    appt = await portal_svc.book_appointment(patient.id, clinic.id, book_req)
    assert appt.id is not None
    assert appt.status == AppointmentStatus.SCHEDULED
    assert appt.reason == "Routine cleaning and scaling checkup"

    # Cancel
    cancel_req = PortalAppointmentCancelRequest(
        cancellation_reason="Travelling for work on that day."
    )
    cancelled = await portal_svc.cancel_appointment(patient.id, clinic.id, appt.id, cancel_req)
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert "Travelling for work" in cancelled.cancellation_reason


@pytest.mark.asyncio
async def test_portal_prescriptions_and_invoices_retrieval(portal_setup):
    clinic, dentist, patient = portal_setup
    rx = Prescription(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        appointment_id=uuid4(),
        treatment_id=uuid4(),
        prescription_number="RX-2026-0001",
        date=date(2026, 9, 5),
        diagnosis="Acute periapical periodontitis",
        notes="Complete the full antibiotic course.",
    )
    rx.dentist = dentist
    rx.items = [
        PrescriptionItem(
            id=uuid4(),
            prescription_id=rx.id,
            medicine_name="Amoxicillin 500mg",
            dosage="1 capsule",
            strength="500mg",
            frequency="TID",
            duration="5 days",
        )
    ]

    db = FakePortalDb([clinic, dentist, patient, rx])
    portal_svc = PatientPortalService(db)

    rxs = await portal_svc.list_prescriptions(patient.id, clinic.id)
    assert len(rxs) == 1
    assert rxs[0].prescription_number == "RX-2026-0001"
    assert len(rxs[0].items) == 1


@pytest.mark.asyncio
async def test_portal_profile_update_and_records(portal_setup):
    clinic, dentist, patient = portal_setup
    tooth = Tooth(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number="11",
        universal_number="8",
        palmer_notation="1|",
        name="Maxillary Right Central Incisor",
        arch="UPPER",
        quadrant=1,
        tooth_type="INCISOR",
        primary_status="HEALTHY",
    )
    doc = PatientDocument(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        file_name="Panorex-2026.pdf",
        content_type="application/pdf",
        storage_key="docs/panorex-2026.pdf",
        document_type="X_RAY",
    )

    db = FakePortalDb([clinic, dentist, patient, tooth, doc])
    portal_svc = PatientPortalService(db)

    # 1. Update Profile
    update_payload = PortalProfileUpdate(
        address="10 Downing Street, London",
        emergency_contact_name="Wilfred Mott",
        emergency_contact_phone="+442079460000",
    )
    updated_patient = await portal_svc.update_profile(patient.id, clinic.id, update_payload)
    assert updated_patient.address == "10 Downing Street, London"
    assert updated_patient.emergency_contact_name == "Wilfred Mott"

    # 2. Odontogram
    teeth = await portal_svc.get_odontogram(patient.id, clinic.id)
    assert len(teeth) == 1
    assert teeth[0].tooth_number == "11"

    # 3. Documents
    docs = await portal_svc.list_documents(patient.id, clinic.id)
    assert len(docs) == 1
    assert docs[0].file_name == "Panorex-2026.pdf"

    # 4. Invoices
    invoices = await portal_svc.list_invoices(patient.id, clinic.id)
    assert isinstance(invoices, list)

