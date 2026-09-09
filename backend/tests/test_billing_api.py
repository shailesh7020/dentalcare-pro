from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import billing as billing_api
from app.models.billing import (
    DiscountType,
    Invoice,
    InvoiceItemType,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.identity import Clinic, Role, User
from app.models.patient import Patient
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


class FakeApiDb:
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

        # Clinic query
        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        # Patient query
        if "from patients" in text:
            patients = [i for i in self.items if isinstance(i, Patient) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: patients[0] if patients else None,
                scalars=lambda: SimpleNamespace(all=lambda: patients),
            )

        # Treatment query
        if "from treatments" in text:
            treatments = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: treatments[0] if treatments else None,
                scalars=lambda: SimpleNamespace(all=lambda: treatments),
            )

        # User query
        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User) and i.deleted_at is None]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
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
async def test_billing_api_complete_workflow():
    clinic_id = uuid4()
    dentist_id = uuid4()
    patient_id = uuid4()

    clinic = Clinic(
        id=clinic_id,
        name="DentalCare Premier Center",
        slug="dentalcare-premier",
        email="contact@dentalcare-pro.in",
        phone="+91 98765 43210",
    )
    dentist = User(
        id=dentist_id,
        clinic_id=clinic_id,
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
    )
    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        first_name="Riya",
        last_name="Kapoor",
        patient_number="P-2026-001",
        mobile_number="9876543210",
        email="riya.kapoor@example.com",
    )

    db = FakeApiDb([clinic, dentist, patient])

    # 1. Create Invoice
    # Subtotal: 500 (consultation) + 4500 (root canal) = 5000
    # Discount: 10% = 500 -> Taxable: 4500
    # Tax: 18% = 810 -> Grand total: 5310.00
    payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        tax_rate=18.0,
        notes="Root canal therapy procedure invoice",
        terms="Payment due upon receipt",
        items=[
            InvoiceItemCreate(
                item_type=InvoiceItemType.CONSULTATION,
                description="Specialist Consultation",
                quantity=1,
                unit_price=500.00,
            ),
            InvoiceItemCreate(
                item_type=InvoiceItemType.PROCEDURE,
                description="Root Canal Therapy #46",
                quantity=1,
                unit_price=4500.00,
            ),
        ],
    )

    created_inv = await billing_api.create_invoice(payload, dentist, db)
    assert created_inv.patient_id == patient_id
    assert created_inv.grand_total == 5310.00
    assert created_inv.balance_due == 5310.00
    assert created_inv.status == InvoiceStatus.UNPAID
    assert len(created_inv.items) == 2

    # 2. Get Invoice Detail
    fetched = await billing_api.get_invoice(created_inv.id, dentist, db)
    assert fetched.id == created_inv.id
    assert fetched.invoice_number == created_inv.invoice_number

    # 3. Update Invoice
    update_payload = InvoiceUpdate(notes="Updated notes: follow up in 7 days")
    updated = await billing_api.update_invoice(created_inv.id, update_payload, dentist, db)
    assert updated.notes == "Updated notes: follow up in 7 days"

    # 4. Download Official PDF Tax Invoice
    pdf_res = await billing_api.download_invoice_pdf(created_inv.id, dentist, db)
    assert pdf_res.media_type == "application/pdf"
    assert pdf_res.body.startswith(b"%PDF-")
    assert len(pdf_res.body) > 1000

    # 5. Record Partial Payment (₹3000 via UPI)
    pay1_payload = PaymentCreate(
        amount=3000.00,
        method=PaymentMethod.UPI,
        transaction_reference="UPI/987654321",
        notes="Initial deposit",
    )
    pay1 = await billing_api.record_payment(created_inv.id, pay1_payload, dentist, db)
    assert pay1.amount == 3000.00
    assert pay1.remaining_balance == 2310.00

    # 6. Download Payment Receipt PDF
    receipt_pdf = await billing_api.download_receipt_pdf(pay1.id, dentist, db)
    assert receipt_pdf.media_type == "application/pdf"
    assert receipt_pdf.body.startswith(b"%PDF-")
    assert len(receipt_pdf.body) > 1000

    # 7. Record Final Payment (₹2310 via CASH -> Fully Paid)
    pay2_payload = PaymentCreate(
        amount=2310.00,
        method=PaymentMethod.CASH,
        notes="Final settlement",
    )
    pay2 = await billing_api.record_payment(created_inv.id, pay2_payload, dentist, db)
    assert pay2.amount == 2310.00
    assert pay2.remaining_balance == 0.00

    # Verify invoice is now PAID
    paid_inv = await billing_api.get_invoice(created_inv.id, dentist, db)
    assert paid_inv.status == InvoiceStatus.PAID
    assert paid_inv.balance_due == 0.00

    # 8. Refund Payment 1 (₹1000 partial refund)
    refund_payload = PaymentRefund(
        refund_amount=1000.00,
        refund_reason="Goodwill insurance adjustment",
    )
    refunded_pay = await billing_api.refund_payment(pay1.id, refund_payload, dentist, db)
    assert refunded_pay.status == PaymentStatus.REFUNDED
    assert refunded_pay.refund_amount == 1000.00

    # Verify invoice status reverted to PARTIALLY_PAID
    reverted_inv = await billing_api.get_invoice(created_inv.id, dentist, db)
    assert reverted_inv.status == InvoiceStatus.PARTIALLY_PAID
    assert reverted_inv.balance_due == 1000.00

    # 9. List Invoices
    inv_list = await billing_api.list_invoices(
        patient_id=None,
        treatment_id=None,
        dentist_id=None,
        status_filter=None,
        date_from=None,
        date_to=None,
        search=None,
        limit=50,
        offset=0,
        actor=dentist,
        db=db,
    )
    assert len(inv_list) >= 1

    # 10. Patient Billing Summary
    summary = await billing_api.get_patient_billing_summary(patient_id, dentist, db)
    assert summary.patient_id == patient_id
    assert summary.invoices_count >= 1

    # 11. Dashboard Stats & Revenue Reports
    stats = await billing_api.get_billing_dashboard_stats(dentist, db)
    assert stats.total_invoices_count >= 1

    rev_report = await billing_api.get_revenue_report(None, None, dentist, db)
    assert isinstance(rev_report.items, list)


@pytest.mark.asyncio
async def test_billing_api_generate_from_treatment():
    clinic_id = uuid4()
    dentist_id = uuid4()
    patient_id = uuid4()
    treatment_id = uuid4()

    clinic = Clinic(id=clinic_id, name="DentalCare Test", slug="dc-test", email="test@dc.com")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Dr", last_name="Sharma", role=Role.DENTIST)
    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Aarav", last_name="Patel", patient_number="P-005")

    proc = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Composite Filling #21",
        quantity=1,
        cost=1500.00,
    )
    treatment = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentist_id=dentist_id,
        treatment_number="TRT-2026-0099",
        diagnosis="Class III caries on #21",
        procedures=[proc],
    )

    db = FakeApiDb([clinic, dentist, patient, treatment])

    gen_payload = InvoiceGenerateFromTreatment(
        consultation_fee=300.00,
        discount_type=DiscountType.FIXED,
        discount_value=100.00,
        tax_rate=0.0,
    )

    inv = await billing_api.generate_invoice_from_treatment(treatment_id, gen_payload, dentist, db)
    assert inv.treatment_id == treatment_id
    # Subtotal: 300 (fee) + 1500 (proc) = 1800 - 100 = 1700
    assert inv.subtotal == 1800.00
    assert inv.grand_total == 1700.00
    assert len(inv.items) == 2


@pytest.mark.asyncio
async def test_billing_api_cancellation_and_immutability():
    clinic_id = uuid4()
    dentist = User(id=uuid4(), clinic_id=clinic_id, first_name="Dr", last_name="Verma", role=Role.DENTIST)

    paid_inv = Invoice(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        dentist_id=dentist.id,
        invoice_number="INV-LOCK-01",
        status=InvoiceStatus.PAID,
        grand_total=1000.00,
        amount_paid=1000.00,
        balance_due=0.00,
        items=[],
        payments=[],
    )
    db = FakeApiDb([paid_inv])

    # Editing paid invoice raises 400
    with pytest.raises(HTTPException) as exc1:
        await billing_api.update_invoice(paid_inv.id, InvoiceUpdate(notes="Edit attempt"), dentist, db)
    assert exc1.value.status_code == 400

    # Cancelling invoice with payments raises 400
    with pytest.raises(HTTPException) as exc2:
        await billing_api.cancel_invoice(paid_inv.id, InvoiceCancel(reason="Cancel attempt"), dentist, db)
    assert exc2.value.status_code == 400


@pytest.mark.asyncio
async def test_billing_api_multi_tenant_isolation():
    clinic_b_id = uuid4()
    dentist_b = User(id=uuid4(), clinic_id=clinic_b_id, first_name="Dr", last_name="Other", role=Role.DENTIST)

    db = FakeApiDb([])

    # Clinic B dentist trying to access nonexistent or foreign invoice must get 404
    with pytest.raises(HTTPException) as exc:
        await billing_api.get_invoice(uuid4(), dentist_b, db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_billing_api_treatment_invoices_and_clinic_context():
    clinic_id = uuid4()
    treatment_id = uuid4()
    dentist = User(id=uuid4(), clinic_id=clinic_id, first_name="Dr", last_name="Jain", role=Role.DENTIST)
    user_no_clinic = User(id=uuid4(), clinic_id=None, first_name="No", last_name="Clinic", role=Role.DENTIST)

    invoice = Invoice(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        dentist_id=dentist.id,
        treatment_id=treatment_id,
        invoice_number="INV-TRT-001",
        status=InvoiceStatus.UNPAID,
        grand_total=1200.00,
        amount_paid=0.00,
        balance_due=1200.00,
        items=[],
        payments=[],
    )
    payment = Payment(
        id=uuid4(),
        clinic_id=clinic_id,
        invoice_id=invoice.id,
        receipt_number="REC-001",
        amount=500.00,
        method=PaymentMethod.CASH,
        received_by=dentist.id,
        status=PaymentStatus.COMPLETED,
    )
    invoice.payments.append(payment)
    db = FakeApiDb([invoice, payment])

    # 1. get_treatment_invoices
    trt_invs = await billing_api.get_treatment_invoices(treatment_id, dentist, db)
    assert len(trt_invs) == 1
    assert trt_invs[0].id == invoice.id

    # 2. get_payment
    pay_detail = await billing_api.get_payment(payment.id, dentist, db)
    assert pay_detail.id == payment.id

    # 3. Missing clinic context raises 400
    with pytest.raises(HTTPException) as exc1:
        await billing_api.get_billing_dashboard_stats(user_no_clinic, db)
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        await billing_api.get_treatment_invoices(treatment_id, user_no_clinic, db)
    assert exc2.value.status_code == 400

