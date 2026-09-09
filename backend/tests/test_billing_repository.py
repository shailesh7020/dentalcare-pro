from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.billing import (
    DiscountType,
    Invoice,
    InvoiceItemType,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.identity import Role, User
from app.models.patient import Patient
from app.models.treatment import Treatment, TreatmentProcedure
from app.repositories.billing_repository import BillingRepository
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceGenerateFromTreatment,
    InvoiceItemCreate,
    PaymentCreate,
)


class FakeBillingDb:
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
                matching = [
                    i for i in self.items if isinstance(i, Invoice) and i.deleted_at is None
                ]
                return SimpleNamespace(scalar_one=lambda: len(matching), one=lambda: SimpleNamespace(total_count=len(matching), total_revenue=sum(float(i.grand_total) for i in matching), pending_payments=sum(float(i.balance_due) for i in matching)))
            if "from payments" in text:
                matching = [
                    i for i in self.items if isinstance(i, Payment) and i.deleted_at is None
                ]
                return SimpleNamespace(scalar_one=lambda: len(matching), scalar_one_or_none=lambda: len(matching))

        # Sum queries
        if "sum(" in text:
            matching_payments = [
                i for i in self.items if isinstance(i, Payment) and i.deleted_at is None and i.status == PaymentStatus.COMPLETED
            ]
            total_sum = sum(float(p.amount) for p in matching_payments)
            return SimpleNamespace(scalar_one=lambda: total_sum, scalar_one_or_none=lambda: total_sum)

        # Invoices query
        if "from invoices" in text:
            matching_invs = [
                i for i in self.items if isinstance(i, Invoice) and i.deleted_at is None
            ]
            first_match = matching_invs[0] if matching_invs else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first_match,
                scalars=lambda: SimpleNamespace(all=lambda: matching_invs),
                one=lambda: SimpleNamespace(total_count=len(matching_invs), total_revenue=sum(float(i.grand_total) for i in matching_invs), pending_payments=sum(float(i.balance_due) for i in matching_invs)),
            )

        # Payments query
        if "from payments" in text:
            matching_pays = [
                i for i in self.items if isinstance(i, Payment) and i.deleted_at is None
            ]
            first_match = matching_pays[0] if matching_pays else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first_match,
                scalars=lambda: SimpleNamespace(all=lambda: matching_pays),
            )

        return SimpleNamespace(
            scalar_one=lambda: 0,
            scalar_one_or_none=lambda: None,
            scalars=lambda: SimpleNamespace(all=list),
        )


@pytest.mark.asyncio
async def test_billing_repository_invoice_and_receipt_numbering():
    clinic_id = uuid4()
    db = FakeBillingDb([])
    repo = BillingRepository(db)

    inv_no = await repo.generate_invoice_number(clinic_id)
    assert inv_no.startswith("INV-")
    assert inv_no.endswith("-0001")

    rec_no = await repo.generate_receipt_number(clinic_id)
    assert rec_no.startswith("REC-")
    assert rec_no.endswith("-0001")


@pytest.mark.asyncio
async def test_billing_repository_create_invoice_and_calculations():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        first_name="Rajesh",
        last_name="Verma",
        patient_number="P-2026-001",
    )
    dentist = User(
        id=dentist_id,
        clinic_id=clinic_id,
        first_name="Ananya",
        last_name="Shah",
        role=Role.DENTIST,
    )

    db = FakeBillingDb([patient, dentist])
    repo = BillingRepository(db)

    # Subtotal: (1 * 500) + (1 * 3000) = 3500
    # Discount: 10% = 350 -> Taxable: 3150
    # Tax: 18% GST = 567 -> Grand Total: 3717.00
    items = [
        InvoiceItemCreate(
            item_type=InvoiceItemType.CONSULTATION,
            description="Initial Dental Examination",
            quantity=1,
            unit_price=500.00,
        ),
        InvoiceItemCreate(
            item_type=InvoiceItemType.PROCEDURE,
            description="Root Canal Therapy #46",
            quantity=1,
            unit_price=3000.00,
        ),
    ]

    payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        tax_rate=18.0,
        notes="Standard fee with 10% discount",
        items=items,
    )

    inv_num = "INV-20260908-0001"
    inv = await repo.create_invoice(clinic_id, payload, dentist, inv_num)

    assert inv.invoice_number == inv_num
    assert inv.subtotal == 3500.00
    assert inv.discount_amount == 350.00
    assert inv.tax_amount == 567.00
    assert inv.grand_total == 3717.00
    assert inv.amount_paid == 0.00
    assert inv.balance_due == 3717.00
    assert inv.status == InvoiceStatus.UNPAID
    assert len(inv.items) == 2


@pytest.mark.asyncio
async def test_billing_repository_payment_lifecycle_and_balance():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()

    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Aarav", last_name="Mehta", patient_number="P-101")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Dr", last_name="Shah", role=Role.DENTIST)

    db = FakeBillingDb([patient, dentist])
    repo = BillingRepository(db)

    # 1. Create Invoice with Grand Total = 2000.00
    payload = InvoiceCreate(
        patient_id=patient_id,
        dentist_id=dentist_id,
        items=[
            InvoiceItemCreate(
                item_type=InvoiceItemType.PROCEDURE,
                description="Dental Scaling",
                quantity=1,
                unit_price=2000.00,
            )
        ],
    )
    inv = await repo.create_invoice(clinic_id, payload, dentist, "INV-20260908-0002")

    # 2. Record Partial Payment: 1000.00
    pay1 = await repo.create_payment(
        clinic_id=clinic_id,
        invoice=inv,
        payload=PaymentCreate(
            amount=1000.00,
            method=PaymentMethod.UPI,
            transaction_reference="UPI/123456789",
        ),
        actor=dentist,
        receipt_number="REC-20260908-0001",
    )
    assert pay1.amount == 1000.00
    assert inv.amount_paid == 1000.00
    assert inv.balance_due == 1000.00
    assert inv.status == InvoiceStatus.PARTIALLY_PAID

    # 3. Record Second Payment: 1000.00 (Full Settlement)
    pay2 = await repo.create_payment(
        clinic_id=clinic_id,
        invoice=inv,
        payload=PaymentCreate(
            amount=1000.00,
            method=PaymentMethod.CASH,
        ),
        actor=dentist,
        receipt_number="REC-20260908-0002",
    )
    assert pay2.amount == 1000.00
    assert inv.amount_paid == 2000.00
    assert inv.balance_due == 0.00
    assert inv.status == InvoiceStatus.PAID

    # 4. Refund pay2: 500.00
    refunded_pay = await repo.refund_payment(
        clinic_id=clinic_id,
        payment=pay2,
        invoice=inv,
        refund_amount=500.00,
        reason="Partial discount retroactively applied",
        actor=dentist,
    )
    assert refunded_pay.status == PaymentStatus.REFUNDED
    assert refunded_pay.refund_amount == 500.00
    assert inv.amount_paid == 1500.00
    assert inv.balance_due == 500.00
    assert inv.status == InvoiceStatus.PARTIALLY_PAID


@pytest.mark.asyncio
async def test_billing_repository_treatment_to_invoice_generation():
    clinic_id = uuid4()
    patient_id = uuid4()
    dentist_id = uuid4()
    treatment_id = uuid4()
    appointment_id = uuid4()

    proc1 = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Extraction Anterior",
        tooth_number="11",
        quantity=1,
        cost=1500.00,
    )
    proc2 = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment_id,
        procedure_name="Composite Restoration",
        tooth_number="21",
        quantity=1,
        cost=1200.00,
    )

    treatment = Treatment(
        id=treatment_id,
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=appointment_id,
        dentist_id=dentist_id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Traumatic fracture 11, 21",
        procedures=[proc1, proc2],
    )

    patient = Patient(id=patient_id, clinic_id=clinic_id, first_name="Sneha", last_name="Patil", patient_number="P-102")
    dentist = User(id=dentist_id, clinic_id=clinic_id, first_name="Dr", last_name="Shah", role=Role.DENTIST)

    db = FakeBillingDb([treatment, patient, dentist])
    repo = BillingRepository(db)

    gen_payload = InvoiceGenerateFromTreatment(
        consultation_fee=300.00,
        discount_type=DiscountType.FIXED,
        discount_value=200.00,
        tax_rate=0.0,
    )

    inv = await repo.create_invoice_from_treatment(
        clinic_id=clinic_id,
        treatment=treatment,
        payload=gen_payload,
        actor=dentist,
        invoice_number="INV-20260908-0003",
    )

    assert inv.invoice_number == "INV-20260908-0003"
    # Subtotal: 300 (consultation) + 1500 (proc1) + 1200 (proc2) = 3000
    assert inv.subtotal == 3000.00
    assert inv.discount_amount == 200.00
    assert inv.grand_total == 2800.00
    assert inv.balance_due == 2800.00
    assert len(inv.items) == 3
