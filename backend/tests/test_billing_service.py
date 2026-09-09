from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.appointment import Appointment
from app.models.billing import (
    DiscountType,
    Invoice,
    InvoiceItemType,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.identity import AuditEvent, Role, User
from app.models.patient import Patient, PatientTimelineEvent
from app.models.treatment import Treatment, TreatmentProcedure
from app.schemas.billing import (
    InvoiceCancel,
    InvoiceCreate,
    InvoiceGenerateFromTreatment,
    InvoiceItemCreate,
    InvoiceUpdate,
    PaymentCreate,
    PaymentRefund,
)
from app.services.billing_service import BillingService


class FakeServiceDb:
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

        # Count queries
        if "count(" in text:
            if "from invoices" in text:
                matching = [i for i in self.items if isinstance(i, Invoice) and i.deleted_at is None]
                return SimpleNamespace(
                    scalar_one=lambda: len(matching),
                    scalar_one_or_none=lambda: len(matching),
                    one=lambda: SimpleNamespace(
                        total_count=len(matching),
                        total_revenue=sum(float(i.grand_total) for i in matching),
                        pending_payments=sum(float(i.balance_due) for i in matching),
                    ),
                )
            if "from payments" in text:
                matching = [i for i in self.items if isinstance(i, Payment) and i.deleted_at is None]
                return SimpleNamespace(scalar_one=lambda: len(matching), scalar_one_or_none=lambda: len(matching))

        # Sum queries
        if "sum(" in text:
            matching_payments = [
                i for i in self.items if isinstance(i, Payment) and i.deleted_at is None and i.status == PaymentStatus.COMPLETED
            ]
            total_sum = sum(float(p.amount) for p in matching_payments)
            return SimpleNamespace(scalar_one=lambda: total_sum, scalar_one_or_none=lambda: total_sum)

        # Patient query
        if "from patients" in text:
            patients = [i for i in self.items if isinstance(i, Patient) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: patients[0] if patients else None,
                scalars=lambda: SimpleNamespace(all=lambda: patients),
            )

        # Dentist / User query
        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        # Treatment query
        if "from treatments" in text:
            treatments = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: treatments[0] if treatments else None,
                scalars=lambda: SimpleNamespace(all=lambda: treatments),
            )

        # Appointment query
        if "from appointments" in text:
            appointments = [i for i in self.items if isinstance(i, Appointment) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: appointments[0] if appointments else None,
                scalars=lambda: SimpleNamespace(all=lambda: appointments),
            )

        # Invoice query
        if "from invoices" in text:
            invoices = [i for i in self.items if isinstance(i, Invoice) and i.deleted_at is None]
            first = invoices[0] if invoices else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: invoices),
                one=lambda: SimpleNamespace(
                    total_count=len(invoices),
                    total_revenue=sum(float(i.grand_total) for i in invoices),
                    pending_payments=sum(float(i.balance_due) for i in invoices),
                ),
            )

        # Payment query
        if "from payments" in text:
            payments = [i for i in self.items if isinstance(i, Payment) and i.deleted_at is None]
            first = payments[0] if payments else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: payments),
            )

        return SimpleNamespace(
            scalar_one=lambda: 0,
            scalar_one_or_none=lambda: None,
            scalars=lambda: SimpleNamespace(all=list),
        )


@pytest.mark.asyncio
async def test_billing_service_create_invoice_success():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Rohan", last_name="Sharma", patient_number="P-001")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Vikram", last_name="Aditya", role=Role.DENTIST)

    db = FakeServiceDb([patient, dentist])
    service = BillingService(db)

    payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        items=[
            InvoiceItemCreate(
                item_type=InvoiceItemType.PROCEDURE,
                description="Dental Prophylaxis",
                quantity=1,
                unit_price=1200.00,
            )
        ],
    )

    detail = await service.create_invoice(clinic_id, payload, dentist)
    assert detail.patient_id == patient_id
    assert detail.grand_total == 1200.00
    assert detail.balance_due == 1200.00
    assert detail.status == InvoiceStatus.UNPAID

    # Verify timeline and audit events were emitted
    timeline_events = [e for e in db.added if isinstance(e, PatientTimelineEvent)]
    assert len(timeline_events) == 1
    assert timeline_events[0].event_type == "INVOICE_GENERATED"

    audit_events = [e for e in db.added if isinstance(e, AuditEvent)]
    assert len(audit_events) == 1
    assert audit_events[0].action == "CREATE"


@pytest.mark.asyncio
async def test_billing_service_validation_errors():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    # Case 1: Patient not found
    db = FakeServiceDb([])
    service = BillingService(db)
    actor = User(id=uuid4(), clinic_id=clinic_id, first_name="Dr", last_name="Who", role=Role.DENTIST)

    payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=100.0)],
    )

    with pytest.raises(HTTPException) as exc1:
        await service.create_invoice(clinic_id, payload, actor)
    assert exc1.value.status_code == 404
    assert "Patient not found" in exc1.value.detail

    # Case 2: Clinician has invalid role (e.g. RECEPTIONIST)
    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Test", last_name="Patient", patient_number="P-002")
    non_dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Non", last_name="Doctor", role=Role.RECEPTIONIST)
    db2 = FakeServiceDb([patient, non_dentist])
    service2 = BillingService(db2)

    with pytest.raises(HTTPException) as exc2:
        await service2.create_invoice(clinic_id, payload, non_dentist)
    assert exc2.value.status_code == 400
    assert "authority" in exc2.value.detail


@pytest.mark.asyncio
async def test_billing_service_generate_from_treatment():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()
    treatment_id = uuid4()

    proc = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Crown Placement #16",
        quantity=1,
        cost=8000.00,
    )
    treatment = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        treatment_number="TRT-100",
        procedures=[proc],
    )
    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Maya", last_name="Sen", patient_number="P-003")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Sanjay", last_name="Gupta", role=Role.DENTIST)

    db = FakeServiceDb([treatment, patient, dentist])
    service = BillingService(db)

    gen_payload = InvoiceGenerateFromTreatment(
        consultation_fee=500.00,
        discount_type=DiscountType.FIXED,
        discount_value=500.00,
        tax_rate=0.0,
    )

    detail = await service.generate_from_treatment(clinic_id, treatment_id, gen_payload, dentist)
    # Total: 500 (consultation) + 8000 (crown) - 500 (discount) = 8000.00
    assert detail.grand_total == 8000.00
    assert detail.treatment_id == treatment_id

    # Verify events
    timeline_events = [e for e in db.added if isinstance(e, PatientTimelineEvent)]
    assert any(e.event_type == "INVOICE_GENERATED" for e in timeline_events)


@pytest.mark.asyncio
async def test_billing_service_paid_invoice_immutability():
    clinic_id = uuid4()
    invoice_id = uuid4()
    actor = User(id=uuid4(), clinic_id=clinic_id, first_name="Dr", last_name="Mehta", role=Role.DENTIST)

    # Invoice that is already PAID
    paid_invoice = Invoice(
        id=invoice_id,
        clinic_id=clinic_id,
        patient_id=uuid4(),
        dentist_id=actor.id,
        invoice_number="INV-PAID-01",
        status=InvoiceStatus.PAID,
        grand_total=5000.00,
        amount_paid=5000.00,
        balance_due=0.00,
        items=[],
        payments=[],
    )

    db = FakeServiceDb([paid_invoice])
    service = BillingService(db)

    # Trying to update a paid invoice MUST raise 400
    with pytest.raises(HTTPException) as exc:
        await service.update_invoice(clinic_id, invoice_id, InvoiceUpdate(notes="Trying to edit"), actor)
    assert exc.value.status_code == 400
    assert "locked and cannot be edited" in exc.value.detail


@pytest.mark.asyncio
async def test_billing_service_cancellation_rules():
    clinic_id = uuid4()
    invoice_id = uuid4()
    patient_id = uuid4()
    actor = User(id=uuid4(), clinic_id=clinic_id, first_name="Admin", last_name="User", role=Role.CLINIC_ADMIN)

    # Invoice with paid amount > 0
    inv_with_pay = Invoice(
        id=invoice_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=actor.id,
        invoice_number="INV-PART-01",
        status=InvoiceStatus.PARTIALLY_PAID,
        grand_total=3000.00,
        amount_paid=1000.00,
        balance_due=2000.00,
        items=[],
        payments=[],
    )

    db = FakeServiceDb([inv_with_pay])
    service = BillingService(db)

    # Cannot cancel when payments exist
    with pytest.raises(HTTPException) as exc:
        await service.cancel_invoice(clinic_id, invoice_id, InvoiceCancel(reason="Mistake"), actor)
    assert exc.value.status_code == 400
    assert "recorded payments" in exc.value.detail

    # Clean invoice without payments can be cancelled
    clean_inv = Invoice(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=actor.id,
        invoice_number="INV-CLEAN-01",
        status=InvoiceStatus.UNPAID,
        grand_total=3000.00,
        amount_paid=0.00,
        balance_due=3000.00,
        items=[],
        payments=[],
    )
    db.items.append(clean_inv)

    cancelled = await service.cancel_invoice(clinic_id, clean_inv.id, InvoiceCancel(reason="Duplicate"), actor)
    assert cancelled.status == InvoiceStatus.CANCELLED
    assert cancelled.cancellation_reason == "Duplicate"


@pytest.mark.asyncio
async def test_billing_service_payment_processing_and_limits():
    clinic_id = uuid4()
    invoice_id = uuid4()
    patient_id = uuid4()
    actor = User(id=uuid4(), clinic_id=clinic_id, first_name="Cashier", last_name="One", role=Role.RECEPTIONIST)

    invoice = Invoice(
        id=invoice_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=actor.id,
        invoice_number="INV-PAY-01",
        status=InvoiceStatus.UNPAID,
        grand_total=2500.00,
        amount_paid=0.00,
        balance_due=2500.00,
        items=[],
        payments=[],
    )

    db = FakeServiceDb([invoice])
    service = BillingService(db)

    # 1. Overpayment rejected
    with pytest.raises(HTTPException) as exc_over:
        await service.record_payment(
            clinic_id,
            invoice_id,
            PaymentCreate(amount=3000.00, method=PaymentMethod.CASH),
            actor,
        )
    assert exc_over.value.status_code == 400
    assert "exceeds outstanding balance" in exc_over.value.detail

    # 2. Valid partial payment
    pay_detail = await service.record_payment(
        clinic_id,
        invoice_id,
        PaymentCreate(amount=1500.00, method=PaymentMethod.CARD, transaction_reference="TXN123"),
        actor,
    )
    assert pay_detail.amount == 1500.00
    assert invoice.balance_due == 1000.00
    assert invoice.status == InvoiceStatus.PARTIALLY_PAID

    # 3. Complete remaining balance
    pay_detail2 = await service.record_payment(
        clinic_id,
        invoice_id,
        PaymentCreate(amount=1000.00, method=PaymentMethod.UPI),
        actor,
    )
    assert pay_detail2.amount == 1000.00
    assert invoice.balance_due == 0.00
    assert invoice.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_billing_service_refund_handling():
    clinic_id = uuid4()
    invoice_id = uuid4()
    patient_id = uuid4()
    payment_id = uuid4()
    actor = User(id=uuid4(), clinic_id=clinic_id, first_name="Clinic", last_name="Manager", role=Role.CLINIC_ADMIN)

    invoice = Invoice(
        id=invoice_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=actor.id,
        invoice_number="INV-REF-01",
        status=InvoiceStatus.PAID,
        grand_total=2000.00,
        amount_paid=2000.00,
        balance_due=0.00,
        items=[],
        payments=[],
    )
    payment = Payment(
        id=payment_id,
        clinic_id=clinic_id,
        invoice_id=invoice_id,
        receipt_number="REC-REF-01",
        amount=2000.00,
        method=PaymentMethod.UPI,
        received_by=actor.id,
        status=PaymentStatus.COMPLETED,
    )
    invoice.payments.append(payment)

    db = FakeServiceDb([invoice, payment])
    service = BillingService(db)

    # 1. Reject refund exceeding original payment
    with pytest.raises(HTTPException) as exc_refund:
        await service.refund_payment(
            clinic_id,
            payment_id,
            PaymentRefund(refund_amount=2500.00, refund_reason="Excess"),
            actor,
        )
    assert exc_refund.value.status_code == 400
    assert "cannot exceed original payment amount" in exc_refund.value.detail

    # 2. Process valid partial refund
    ref_detail = await service.refund_payment(
        clinic_id,
        payment_id,
        PaymentRefund(refund_amount=500.00, refund_reason="Service discount adjusted post-care"),
        actor,
    )
    assert ref_detail.status == PaymentStatus.REFUNDED
    assert ref_detail.refund_amount == 500.00
    assert invoice.amount_paid == 1500.00
    assert invoice.balance_due == 500.00
    assert invoice.status == InvoiceStatus.PARTIALLY_PAID


@pytest.mark.asyncio
async def test_billing_service_additional_branches():
    clinic_id = uuid4()
    patient_id = uuid4()
    other_patient_id = uuid4()
    dentist_id = uuid4()
    treatment_id = uuid4()
    appointment_id = uuid4()

    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="A", last_name="B")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="D", last_name="E", role=Role.DENTIST)
    trt_mismatch = Treatment(id=treatment_id, clinic_id=clinic_id, patient_id=other_patient_id, dentist_id=dentist_id)
    apt_mismatch = Appointment(id=appointment_id, clinic_id=clinic_id, patient_id=other_patient_id, dentist_id=dentist_id)

    db = FakeServiceDb([patient, dentist, trt_mismatch, apt_mismatch])
    service = BillingService(db)

    # Empty items
    empty_payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        items=[InvoiceItemCreate(description="Temp", quantity=1, unit_price=10.0)],
    )
    empty_payload.items = []
    with pytest.raises(HTTPException) as exc1:
        await service.create_invoice(
            clinic_id,
            empty_payload,
            dentist,
        )
    assert exc1.value.status_code == 400

    # Treatment mismatch
    with pytest.raises(HTTPException) as exc2:
        await service.create_invoice(
            clinic_id,
            InvoiceCreate(
                patient_id=patient_id,
                dentist_id=dentist_id,
                treatment_id=treatment_id,
                items=[InvoiceItemCreate(description="D", quantity=1, unit_price=10.0)],
            ),
            dentist,
        )
    assert exc2.value.status_code == 400
    assert "does not belong" in exc2.value.detail

    # Appointment mismatch
    with pytest.raises(HTTPException) as exc3:
        await service.create_invoice(
            clinic_id,
            InvoiceCreate(
                patient_id=patient_id,
                dentist_id=dentist_id,
                appointment_id=appointment_id,
                items=[InvoiceItemCreate(description="D", quantity=1, unit_price=10.0)],
            ),
            dentist,
        )
    assert exc3.value.status_code == 400
    assert "does not belong" in exc3.value.detail

    # Non-existent invoice / payment / patient
    with pytest.raises(HTTPException) as exc4:
        await service.get_invoice(clinic_id, uuid4())
    assert exc4.value.status_code == 404

    with pytest.raises(HTTPException) as exc5:
        await service.get_payment(clinic_id, uuid4())
    assert exc5.value.status_code == 404

    # Cancel already cancelled invoice
    cancelled_inv = Invoice(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        invoice_number="INV-C-1",
        status=InvoiceStatus.CANCELLED,
        items=[],
        payments=[],
    )
    db.items.append(cancelled_inv)
    with pytest.raises(HTTPException) as exc6:
        await service.cancel_invoice(clinic_id, cancelled_inv.id, InvoiceCancel(reason="Again"), dentist)
    assert exc6.value.status_code == 400
    assert "already cancelled" in exc6.value.detail

    # Record payment on cancelled invoice
    with pytest.raises(HTTPException) as exc7:
        await service.record_payment(
            clinic_id,
            cancelled_inv.id,
            PaymentCreate(amount=100.0, method=PaymentMethod.CASH),
            dentist,
        )
    assert exc7.value.status_code == 400
    assert "cancelled invoice" in exc7.value.detail

    # Refund already refunded payment
    refunded_payment = Payment(
        id=uuid4(),
        clinic_id=clinic_id,
        invoice_id=cancelled_inv.id,
        receipt_number="REC-R-1",
        amount=100.0,
        status=PaymentStatus.REFUNDED,
    )
    db.items.append(refunded_payment)
    with pytest.raises(HTTPException) as exc8:
        await service.refund_payment(
            clinic_id,
            refunded_payment.id,
            PaymentRefund(refund_amount=50.0, refund_reason="Again"),
            dentist,
        )
    assert exc8.value.status_code == 400
    assert "already been refunded" in exc8.value.detail

