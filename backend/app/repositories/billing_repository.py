from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.billing import (
    DiscountType,
    Invoice,
    InvoiceItem,
    InvoiceItemType,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.identity import User
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.billing import (
    BillingDashboardStats,
    InvoiceCreate,
    InvoiceDetail,
    InvoiceGenerateFromTreatment,
    InvoiceItemCreate,
    InvoiceItemRead,
    InvoiceUpdate,
    PaymentCreate,
    PaymentDetail,
    PaymentRead,
    RevenueReport,
    RevenueReportItem,
)


class BillingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_invoice_query(self, clinic_id: UUID):
        return (
            select(Invoice)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.deleted_at.is_(None),
            )
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.payments),
                selectinload(Invoice.patient),
                selectinload(Invoice.dentist),
                selectinload(Invoice.treatment),
                selectinload(Invoice.appointment),
                selectinload(Invoice.clinic),
            )
        )

    def _base_payment_query(self, clinic_id: UUID):
        return (
            select(Payment)
            .where(
                Payment.clinic_id == clinic_id,
                Payment.deleted_at.is_(None),
            )
            .options(
                selectinload(Payment.invoice).selectinload(Invoice.patient),
                selectinload(Payment.receiver),
                selectinload(Payment.clinic),
            )
        )

    async def generate_invoice_number(
        self, clinic_id: UUID, target_date: date | None = None
    ) -> str:
        d = target_date or datetime.now(UTC).date()
        prefix = f"INV-{d.strftime('%Y%m%d')}"
        query = select(func.count(Invoice.id)).where(
            Invoice.clinic_id == clinic_id,
            Invoice.invoice_number.like(f"{prefix}-%"),
        )
        res = await self.db.execute(query)
        count = res.scalar_one() or 0
        return f"{prefix}-{count + 1:04d}"

    async def generate_receipt_number(
        self, clinic_id: UUID, target_date: date | None = None
    ) -> str:
        d = target_date or datetime.now(UTC).date()
        prefix = f"REC-{d.strftime('%Y%m%d')}"
        query = select(func.count(Payment.id)).where(
            Payment.clinic_id == clinic_id,
            Payment.receipt_number.like(f"{prefix}-%"),
        )
        res = await self.db.execute(query)
        count = res.scalar_one() or 0
        return f"{prefix}-{count + 1:04d}"

    async def get_invoice_by_id(
        self, clinic_id: UUID, invoice_id: UUID
    ) -> Invoice | None:
        rx = await self.db.get(Invoice, invoice_id)
        if rx and rx.clinic_id == clinic_id and rx.deleted_at is None:
            if not getattr(rx, "patient", None) and getattr(rx, "patient_id", None):
                rx.patient = await self.db.get(Patient, rx.patient_id)
            if not getattr(rx, "dentist", None) and getattr(rx, "dentist_id", None):
                rx.dentist = await self.db.get(User, rx.dentist_id)
            if not getattr(rx, "treatment", None) and getattr(rx, "treatment_id", None):
                rx.treatment = await self.db.get(Treatment, rx.treatment_id)
            return rx

        query = self._base_invoice_query(clinic_id).where(Invoice.id == invoice_id)
        res = await self.db.execute(query)
        inv = res.scalar_one_or_none()
        if inv:
            if not getattr(inv, "patient", None) and getattr(inv, "patient_id", None):
                inv.patient = await self.db.get(Patient, inv.patient_id)
            if not getattr(inv, "dentist", None) and getattr(inv, "dentist_id", None):
                inv.dentist = await self.db.get(User, inv.dentist_id)
            if not getattr(inv, "treatment", None) and getattr(inv, "treatment_id", None):
                inv.treatment = await self.db.get(Treatment, inv.treatment_id)
        return inv

    async def get_invoice_by_number(
        self, clinic_id: UUID, invoice_number: str
    ) -> Invoice | None:
        query = self._base_invoice_query(clinic_id).where(
            Invoice.invoice_number == invoice_number
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_invoices(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        treatment_id: UUID | None = None,
        dentist_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        query = self._base_invoice_query(clinic_id)

        if patient_id:
            query = query.where(Invoice.patient_id == patient_id)
        if treatment_id:
            query = query.where(Invoice.treatment_id == treatment_id)
        if dentist_id:
            query = query.where(Invoice.dentist_id == dentist_id)
        if status:
            query = query.where(Invoice.status == status)
        if date_from:
            query = query.where(Invoice.date >= date_from)
        if date_to:
            query = query.where(Invoice.date <= date_to)
        if search:
            query = query.join(Invoice.patient).where(
                or_(
                    Invoice.invoice_number.ilike(f"%{search}%"),
                    Patient.first_name.ilike(f"%{search}%"),
                    Patient.last_name.ilike(f"%{search}%"),
                    Patient.patient_number.ilike(f"%{search}%"),
                )
            )

        query = query.order_by(Invoice.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    def _calculate_totals(
        self,
        items: list[InvoiceItemCreate],
        discount_type: DiscountType,
        discount_value: float,
        tax_rate: float,
    ) -> tuple[float, float, float, float]:
        subtotal = 0.0
        for it in items:
            line_cost = round(it.quantity * float(it.unit_price), 2)
            subtotal += line_cost

        subtotal = round(subtotal, 2)

        if discount_type == DiscountType.PERCENTAGE:
            disc_amount = round(subtotal * (float(discount_value) / 100.0), 2)
        else:
            disc_amount = round(min(subtotal, float(discount_value)), 2)

        taxable = max(0.0, subtotal - disc_amount)
        if tax_rate > 0.0:
            tax_amount = round(taxable * (float(tax_rate) / 100.0), 2)
        else:
            tax_amount = 0.0

        grand_total = round(taxable + tax_amount, 2)
        return subtotal, disc_amount, tax_amount, grand_total

    async def create_invoice(
        self,
        clinic_id: UUID,
        payload: InvoiceCreate,
        actor: User,
        invoice_number: str,
    ) -> Invoice:
        subtotal, disc_amount, tax_amount, grand_total = self._calculate_totals(
            payload.items,
            payload.discount_type,
            payload.discount_value,
            payload.tax_rate,
        )

        inv_date = payload.date or datetime.now(UTC).date()
        inv = Invoice(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            treatment_id=payload.treatment_id,
            dentist_id=payload.dentist_id,
            invoice_number=invoice_number,
            date=inv_date,
            due_date=payload.due_date,
            status=InvoiceStatus.UNPAID,
            subtotal=subtotal,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            discount_amount=disc_amount,
            tax_rate=payload.tax_rate,
            tax_amount=tax_amount,
            grand_total=grand_total,
            amount_paid=0.00,
            balance_due=grand_total,
            notes=payload.notes,
            terms=payload.terms,
            created_by=actor.id,
            updated_by=actor.id,
            version=1,
        )
        self.db.add(inv)
        await self.db.flush()

        for it in payload.items:
            line_subtotal = round(it.quantity * float(it.unit_price), 2)
            it_tax = it.tax_amount
            if it.tax_rate > 0.0 and it_tax == 0.0:
                it_tax = round(
                    (line_subtotal - it.discount_amount)
                    * (float(it.tax_rate) / 100.0),
                    2,
                )
            line_total = round(line_subtotal - it.discount_amount + it_tax, 2)

            item = InvoiceItem(
                invoice=inv,
                invoice_id=inv.id,
                item_type=it.item_type,
                description=it.description,
                quantity=it.quantity,
                unit_price=it.unit_price,
                discount_amount=it.discount_amount,
                tax_rate=it.tax_rate,
                tax_amount=it_tax,
                total=line_total,
                procedure_id=it.procedure_id,
                created_by=actor.id,
                updated_by=actor.id,
                version=1,
            )
            self.db.add(item)

        await self.db.flush()
        return inv

    async def create_invoice_from_treatment(
        self,
        clinic_id: UUID,
        treatment: Treatment,
        payload: InvoiceGenerateFromTreatment,
        actor: User,
        invoice_number: str,
    ) -> Invoice:
        items_to_create: list[InvoiceItemCreate] = []

        if payload.consultation_fee > 0.0:
            items_to_create.append(
                InvoiceItemCreate(
                    item_type=InvoiceItemType.CONSULTATION,
                    description="Clinical Dental Consultation",
                    quantity=1,
                    unit_price=payload.consultation_fee,
                )
            )

        for proc in treatment.procedures or []:
            desc = (
                f"{proc.procedure_name} (Tooth #{proc.tooth_number})"
                if proc.tooth_number
                else proc.procedure_name
            )
            items_to_create.append(
                InvoiceItemCreate(
                    item_type=InvoiceItemType.PROCEDURE,
                    description=desc,
                    quantity=proc.quantity,
                    unit_price=float(proc.cost),
                    procedure_id=proc.id,
                )
            )

        if not items_to_create:
            items_to_create.append(
                InvoiceItemCreate(
                    item_type=InvoiceItemType.PROCEDURE,
                    description=f"Treatment {treatment.treatment_number}: {treatment.diagnosis}",
                    quantity=1,
                    unit_price=0.00,
                )
            )

        inv_payload = InvoiceCreate(
            patient_id=treatment.patient_id,
            appointment_id=treatment.appointment_id,
            treatment_id=treatment.id,
            dentist_id=treatment.dentist_id,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            tax_rate=payload.tax_rate,
            notes=payload.notes or f"Generated from Treatment #{treatment.treatment_number}",
            terms=payload.terms,
            due_date=payload.due_date,
            items=items_to_create,
        )

        return await self.create_invoice(
            clinic_id, inv_payload, actor, invoice_number
        )

    async def update_invoice(
        self,
        clinic_id: UUID,
        invoice: Invoice,
        payload: InvoiceUpdate,
        actor: User,
    ) -> Invoice:
        if payload.due_date is not None:
            invoice.due_date = payload.due_date
        if payload.notes is not None:
            invoice.notes = payload.notes
        if payload.terms is not None:
            invoice.terms = payload.terms

        disc_type = payload.discount_type or invoice.discount_type
        disc_val = (
            payload.discount_value
            if payload.discount_value is not None
            else invoice.discount_value
        )
        t_rate = (
            payload.tax_rate if payload.tax_rate is not None else invoice.tax_rate
        )

        if payload.items is not None:
            # Delete old items
            for old_it in list(invoice.items or []):
                await self.db.delete(old_it)

            invoice.items = []
            for it in payload.items:
                line_subtotal = round(it.quantity * float(it.unit_price), 2)
                it_tax = it.tax_amount
                if it.tax_rate > 0.0 and it_tax == 0.0:
                    it_tax = round(
                        (line_subtotal - it.discount_amount)
                        * (float(it.tax_rate) / 100.0),
                        2,
                    )
                line_total = round(line_subtotal - it.discount_amount + it_tax, 2)

                item = InvoiceItem(
                    invoice=invoice,
                    invoice_id=invoice.id,
                    item_type=it.item_type,
                    description=it.description,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    discount_amount=it.discount_amount,
                    tax_rate=it.tax_rate,
                    tax_amount=it_tax,
                    total=line_total,
                    procedure_id=it.procedure_id,
                    created_by=actor.id,
                    updated_by=actor.id,
                    version=1,
                )
                self.db.add(item)
                invoice.items.append(item)

            subtotal, disc_amount, tax_amount, grand_total = self._calculate_totals(
                payload.items, disc_type, disc_val, t_rate
            )
        else:
            items_to_calc = [
                InvoiceItemCreate(
                    item_type=it.item_type,
                    description=it.description,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    discount_amount=it.discount_amount,
                    tax_rate=it.tax_rate,
                    tax_amount=it.tax_amount,
                )
                for it in invoice.items or []
            ]
            subtotal, disc_amount, tax_amount, grand_total = self._calculate_totals(
                items_to_calc, disc_type, disc_val, t_rate
            )

        invoice.subtotal = subtotal
        invoice.discount_type = disc_type
        invoice.discount_value = disc_val
        invoice.discount_amount = disc_amount
        invoice.tax_rate = t_rate
        invoice.tax_amount = tax_amount
        invoice.grand_total = grand_total
        invoice.balance_due = max(0.00, round(grand_total - invoice.amount_paid, 2))
        invoice.updated_by = actor.id
        invoice.version = (invoice.version or 1) + 1

        if invoice.balance_due <= 0.00 and invoice.amount_paid > 0.00:
            invoice.status = InvoiceStatus.PAID
        elif invoice.amount_paid > 0.00:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        else:
            invoice.status = InvoiceStatus.UNPAID

        await self.db.flush()
        return invoice

    async def cancel_invoice(
        self, clinic_id: UUID, invoice: Invoice, reason: str, actor: User
    ) -> Invoice:
        invoice.status = InvoiceStatus.CANCELLED
        invoice.cancellation_reason = reason
        invoice.updated_by = actor.id
        invoice.version = (invoice.version or 1) + 1
        await self.db.flush()
        return invoice

    async def create_payment(
        self,
        clinic_id: UUID,
        invoice: Invoice,
        payload: PaymentCreate,
        actor: User,
        receipt_number: str,
    ) -> Payment:
        pay_date = payload.payment_date or datetime.now(UTC).date()

        payment = Payment(
            clinic_id=clinic_id,
            invoice_id=invoice.id,
            receipt_number=receipt_number,
            payment_date=pay_date,
            amount=round(payload.amount, 2),
            method=payload.method,
            transaction_reference=payload.transaction_reference,
            notes=payload.notes,
            received_by=actor.id,
            status=PaymentStatus.COMPLETED,
            refund_amount=0.00,
            created_by=actor.id,
            updated_by=actor.id,
            version=1,
        )
        self.db.add(payment)

        # Update invoice balance and status
        invoice.amount_paid = round(invoice.amount_paid + payload.amount, 2)
        invoice.balance_due = max(0.00, round(invoice.grand_total - invoice.amount_paid, 2))
        if invoice.balance_due <= 0.00:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        invoice.updated_by = actor.id
        invoice.version = (invoice.version or 1) + 1

        await self.db.flush()
        return payment

    async def refund_payment(
        self,
        clinic_id: UUID,
        payment: Payment,
        invoice: Invoice,
        refund_amount: float,
        reason: str,
        actor: User,
    ) -> Payment:
        payment.status = PaymentStatus.REFUNDED
        payment.refund_amount = round(refund_amount, 2)
        payment.refund_reason = reason
        payment.refunded_at = datetime.now(UTC)
        payment.refunded_by = actor.id
        payment.updated_by = actor.id
        payment.version = (payment.version or 1) + 1

        # Recalculate invoice amounts
        invoice.amount_paid = max(0.00, round(invoice.amount_paid - refund_amount, 2))
        invoice.balance_due = round(invoice.grand_total - invoice.amount_paid, 2)

        if invoice.amount_paid <= 0.00:
            invoice.status = InvoiceStatus.REFUNDED
        elif invoice.balance_due > 0.00:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        else:
            invoice.status = InvoiceStatus.PAID

        invoice.updated_by = actor.id
        invoice.version = (invoice.version or 1) + 1

        await self.db.flush()
        return payment

    async def get_payment_by_id(
        self, clinic_id: UUID, payment_id: UUID
    ) -> Payment | None:
        p = await self.db.get(Payment, payment_id)
        if p and p.clinic_id == clinic_id and p.deleted_at is None:
            if not getattr(p, "invoice", None) and getattr(p, "invoice_id", None):
                p.invoice = await self.get_invoice_by_id(clinic_id, p.invoice_id)
            if not getattr(p, "receiver", None) and getattr(p, "received_by", None):
                p.receiver = await self.db.get(User, p.received_by)
            return p

        query = self._base_payment_query(clinic_id).where(Payment.id == payment_id)
        res = await self.db.execute(query)
        pay = res.scalar_one_or_none()
        if pay:
            if not getattr(pay, "invoice", None) and getattr(pay, "invoice_id", None):
                pay.invoice = await self.get_invoice_by_id(clinic_id, pay.invoice_id)
            if not getattr(pay, "receiver", None) and getattr(pay, "received_by", None):
                pay.receiver = await self.db.get(User, pay.received_by)
        return pay

    async def list_payments_by_invoice(
        self, clinic_id: UUID, invoice_id: UUID
    ) -> list[Payment]:
        query = (
            self._base_payment_query(clinic_id)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date.asc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_payments_by_patient(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[Payment]:
        query = (
            self._base_payment_query(clinic_id)
            .join(Payment.invoice)
            .where(Invoice.patient_id == patient_id)
            .order_by(Payment.payment_date.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_dashboard_stats(self, clinic_id: UUID) -> BillingDashboardStats:
        today = datetime.now(UTC).date()
        first_of_month = date(today.year, today.month, 1)

        # Invoices stats
        inv_query = select(
            func.count(Invoice.id).label("total_count"),
            func.coalesce(func.sum(Invoice.grand_total), 0.0).label("total_revenue"),
            func.coalesce(func.sum(Invoice.balance_due), 0.0).label("pending_payments"),
        ).where(
            Invoice.clinic_id == clinic_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != InvoiceStatus.CANCELLED,
        )
        inv_res = await self.db.execute(inv_query)
        inv_row = inv_res.one()

        # Outstanding invoices count
        out_query = select(func.count(Invoice.id)).where(
            Invoice.clinic_id == clinic_id,
            Invoice.deleted_at.is_(None),
            Invoice.status.in_([InvoiceStatus.UNPAID, InvoiceStatus.PARTIALLY_PAID]),
        )
        out_res = await self.db.execute(out_query)
        outstanding_count = out_res.scalar_one() or 0

        # Paid invoices count
        paid_query = select(func.count(Invoice.id)).where(
            Invoice.clinic_id == clinic_id,
            Invoice.deleted_at.is_(None),
            Invoice.status == InvoiceStatus.PAID,
        )
        paid_res = await self.db.execute(paid_query)
        paid_count = paid_res.scalar_one() or 0

        # Today payments
        today_pay = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.clinic_id == clinic_id,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.COMPLETED,
            Payment.payment_date == today,
        )
        today_res = await self.db.execute(today_pay)
        today_rev = float(today_res.scalar_one() or 0.0)

        # Monthly payments
        month_pay = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.clinic_id == clinic_id,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.COMPLETED,
            Payment.payment_date >= first_of_month,
        )
        month_res = await self.db.execute(month_pay)
        month_rev = float(month_res.scalar_one() or 0.0)

        # Cash vs Digital
        cash_query = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.clinic_id == clinic_id,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.COMPLETED,
            Payment.method == PaymentMethod.CASH,
        )
        cash_res = await self.db.execute(cash_query)
        cash_coll = float(cash_res.scalar_one() or 0.0)

        dig_query = select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.clinic_id == clinic_id,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.COMPLETED,
            Payment.method != PaymentMethod.CASH,
        )
        dig_res = await self.db.execute(dig_query)
        dig_coll = float(dig_res.scalar_one() or 0.0)

        return BillingDashboardStats(
            total_revenue=float(inv_row.total_revenue),
            today_revenue=today_rev,
            monthly_revenue=month_rev,
            pending_payments=float(inv_row.pending_payments),
            outstanding_invoices_count=outstanding_count,
            paid_invoices_count=paid_count,
            total_invoices_count=inv_row.total_count or 0,
            cash_collections=cash_coll,
            digital_collections=dig_coll,
        )

    async def get_revenue_report(
        self,
        clinic_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> RevenueReport:
        invoices = await self.list_invoices(
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            limit=500,
        )

        total_invoiced = sum(inv.grand_total for inv in invoices if inv.status != InvoiceStatus.CANCELLED)
        total_collected = sum(inv.amount_paid for inv in invoices if inv.status != InvoiceStatus.CANCELLED)
        total_outstanding = sum(inv.balance_due for inv in invoices if inv.status != InvoiceStatus.CANCELLED)

        # Group by month
        periods: dict[str, dict[str, float]] = {}
        for inv in invoices:
            if inv.status == InvoiceStatus.CANCELLED:
                continue
            p = inv.date.strftime("%Y-%m")
            if p not in periods:
                periods[p] = {"invoiced": 0.0, "collected": 0.0, "outstanding": 0.0, "count": 0}
            periods[p]["invoiced"] += float(inv.grand_total)
            periods[p]["collected"] += float(inv.amount_paid)
            periods[p]["outstanding"] += float(inv.balance_due)
            periods[p]["count"] += 1

        items = [
            RevenueReportItem(
                period=k,
                total_invoiced=round(v["invoiced"], 2),
                total_collected=round(v["collected"], 2),
                balance_outstanding=round(v["outstanding"], 2),
                invoices_count=int(v["count"]),
            )
            for k, v in sorted(periods.items())
        ]

        # Collections by method
        pay_query = select(Payment).where(
            Payment.clinic_id == clinic_id,
            Payment.deleted_at.is_(None),
            Payment.status == PaymentStatus.COMPLETED,
        )
        if date_from:
            pay_query = pay_query.where(Payment.payment_date >= date_from)
        if date_to:
            pay_query = pay_query.where(Payment.payment_date <= date_to)

        pay_res = await self.db.execute(pay_query)
        payments = list(pay_res.scalars().all())

        by_method: dict[str, float] = {}
        for p in payments:
            m = str(p.method)
            by_method[m] = round(by_method.get(m, 0.0) + float(p.amount), 2)

        # Dentist revenue
        by_dentist: dict[str, float] = {}
        for inv in invoices:
            if inv.status == InvoiceStatus.CANCELLED:
                continue
            d_name = (
                f"Dr. {inv.dentist.first_name} {inv.dentist.last_name}"
                if inv.dentist
                else "Unknown"
            )
            by_dentist[d_name] = round(by_dentist.get(d_name, 0.0) + float(inv.grand_total), 2)

        return RevenueReport(
            items=items,
            total_invoiced=round(total_invoiced, 2),
            total_collected=round(total_collected, 2),
            total_outstanding=round(total_outstanding, 2),
            collections_by_method=by_method,
            dentist_revenue=by_dentist,
        )

    def to_invoice_detail(self, invoice: Invoice) -> InvoiceDetail:
        items_read = [
            InvoiceItemRead(
                id=item.id,
                invoice_id=item.invoice_id,
                item_type=item.item_type,
                description=item.description,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                discount_amount=float(item.discount_amount),
                tax_rate=float(item.tax_rate),
                tax_amount=float(item.tax_amount),
                total=float(item.total),
                procedure_id=item.procedure_id,
                created_at=item.created_at or datetime.now(UTC),
                updated_at=item.updated_at or datetime.now(UTC),
            )
            for item in (invoice.items or [])
            if item.deleted_at is None
        ]

        payments_read = [
            PaymentRead(
                id=p.id,
                clinic_id=p.clinic_id,
                invoice_id=p.invoice_id,
                receipt_number=p.receipt_number,
                payment_date=p.payment_date,
                amount=float(p.amount),
                method=p.method,
                transaction_reference=p.transaction_reference,
                notes=p.notes,
                received_by=p.received_by,
                status=p.status,
                refund_amount=float(p.refund_amount or 0.0),
                refund_reason=p.refund_reason,
                refunded_at=p.refunded_at,
                refunded_by=p.refunded_by,
                created_at=p.created_at or datetime.now(UTC),
                updated_at=p.updated_at or datetime.now(UTC),
            )
            for p in (invoice.payments or [])
            if p.deleted_at is None
        ]

        patient_name = (
            f"{invoice.patient.first_name} {invoice.patient.last_name}"
            if invoice.patient
            else None
        )
        dentist_name = (
            f"Dr. {invoice.dentist.first_name} {invoice.dentist.last_name}"
            if invoice.dentist
            else None
        )
        treatment_num = (
            invoice.treatment.treatment_number if invoice.treatment else None
        )
        apt_num = (
            invoice.appointment.appointment_number if invoice.appointment else None
        )

        return InvoiceDetail(
            id=invoice.id,
            clinic_id=invoice.clinic_id,
            patient_id=invoice.patient_id,
            appointment_id=invoice.appointment_id,
            treatment_id=invoice.treatment_id,
            dentist_id=invoice.dentist_id,
            invoice_number=invoice.invoice_number,
            date=invoice.date,
            due_date=invoice.due_date,
            status=invoice.status,
            subtotal=float(invoice.subtotal or 0.0),
            discount_type=invoice.discount_type or DiscountType.FIXED,
            discount_value=float(invoice.discount_value or 0.0),
            discount_amount=float(invoice.discount_amount or 0.0),
            tax_rate=float(invoice.tax_rate or 0.0),
            tax_amount=float(invoice.tax_amount or 0.0),
            grand_total=float(invoice.grand_total or 0.0),
            amount_paid=float(invoice.amount_paid or 0.0),
            balance_due=float(invoice.balance_due or 0.0),
            notes=invoice.notes,
            terms=invoice.terms,
            cancellation_reason=invoice.cancellation_reason,
            version=invoice.version or 1,
            created_at=invoice.created_at or datetime.now(UTC),
            updated_at=invoice.updated_at or datetime.now(UTC),
            items=items_read,
            payments=payments_read,
            patient_name=patient_name,
            patient_number=invoice.patient.patient_number if invoice.patient else None,
            patient_phone=invoice.patient.mobile_number if invoice.patient else None,
            patient_email=invoice.patient.email if invoice.patient else None,
            dentist_name=dentist_name,
            treatment_number=treatment_num,
            appointment_number=apt_num,
            clinic_name=invoice.clinic.name if invoice.clinic else None,
            clinic_phone=invoice.clinic.phone if invoice.clinic else None,
            clinic_email=invoice.clinic.email if invoice.clinic else None,
            clinic_address=invoice.clinic.address if invoice.clinic else None,
        )

    def to_payment_detail(
        self, payment: Payment, invoice: Invoice | None = None
    ) -> PaymentDetail:
        inv = invoice or payment.invoice
        receiver_name = (
            f"{payment.receiver.first_name} {payment.receiver.last_name}"
            if payment.receiver
            else None
        )

        pat_name = None
        pat_num = None
        inv_num = None
        balance = 0.00

        if inv:
            inv_num = inv.invoice_number
            balance = float(inv.balance_due)
            if inv.patient:
                pat_name = f"{inv.patient.first_name} {inv.patient.last_name}"
                pat_num = inv.patient.patient_number

        return PaymentDetail(
            id=payment.id,
            clinic_id=payment.clinic_id,
            invoice_id=payment.invoice_id,
            receipt_number=payment.receipt_number,
            payment_date=payment.payment_date,
            amount=float(payment.amount),
            method=payment.method,
            transaction_reference=payment.transaction_reference,
            notes=payment.notes,
            received_by=payment.received_by,
            status=payment.status,
            refund_amount=float(payment.refund_amount or 0.0),
            refund_reason=payment.refund_reason,
            refunded_at=payment.refunded_at,
            refunded_by=payment.refunded_by,
            created_at=payment.created_at or datetime.now(UTC),
            updated_at=payment.updated_at or datetime.now(UTC),
            receiver_name=receiver_name,
            invoice_number=inv_num,
            patient_name=pat_name,
            patient_number=pat_num,
            clinic_name=payment.clinic.name if payment.clinic else None,
            clinic_phone=payment.clinic.phone if payment.clinic else None,
            clinic_email=payment.clinic.email if payment.clinic else None,
            remaining_balance=balance,
        )
