from __future__ import annotations

import json
from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment
from app.models.billing import (
    InvoiceStatus,
    PaymentStatus,
)
from app.models.identity import AuditEvent, Role, User
from app.models.patient import Patient, PatientTimelineEvent
from app.models.treatment import Treatment
from app.repositories.billing_repository import BillingRepository
from app.schemas.billing import (
    BillingDashboardStats,
    InvoiceCancel,
    InvoiceCreate,
    InvoiceDetail,
    InvoiceGenerateFromTreatment,
    InvoiceUpdate,
    PatientBillingSummary,
    PaymentCreate,
    PaymentDetail,
    PaymentRefund,
    RevenueReport,
)


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BillingRepository(db)

    async def _validate_entities(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        dentist_id: UUID,
        treatment_id: UUID | None = None,
        appointment_id: UUID | None = None,
    ) -> tuple[Patient, User, Treatment | None, Appointment | None]:
        # 1. Patient
        patient_q = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        patient_res = await self.db.execute(patient_q)
        patient = patient_res.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found in this clinic.",
            )

        # 2. Dentist
        dentist_q = select(User).where(
            User.id == dentist_id,
            User.clinic_id == clinic_id,
            User.deleted_at.is_(None),
        )
        dentist_res = await self.db.execute(dentist_q)
        dentist = dentist_res.scalar_one_or_none()
        if not dentist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinician not found in this clinic.",
            )
        if dentist.role not in [Role.DENTIST, Role.CLINIC_ADMIN, Role.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have billing/clinical authority.",
            )

        # 3. Treatment (optional)
        treatment: Treatment | None = None
        if treatment_id:
            trt_q = select(Treatment).where(
                Treatment.id == treatment_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
            trt_res = await self.db.execute(trt_q)
            treatment = trt_res.scalar_one_or_none()
            if not treatment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Treatment record not found in this clinic.",
                )
            if treatment.patient_id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Treatment does not belong to specified patient.",
                )

        # 4. Appointment (optional)
        appointment: Appointment | None = None
        if appointment_id:
            apt_q = select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.clinic_id == clinic_id,
                Appointment.deleted_at.is_(None),
            )
            apt_res = await self.db.execute(apt_q)
            appointment = apt_res.scalar_one_or_none()
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment record not found in this clinic.",
                )
            if appointment.patient_id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Appointment does not belong to specified patient.",
                )

        return patient, dentist, treatment, appointment

    async def create_invoice(
        self, clinic_id: UUID, payload: InvoiceCreate, actor: User
    ) -> InvoiceDetail:
        patient, dentist, _treatment, _apt = await self._validate_entities(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            dentist_id=payload.dentist_id,
            treatment_id=payload.treatment_id,
            appointment_id=payload.appointment_id,
        )

        if not payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An invoice must contain at least one line item.",
            )

        inv_number = await self.repo.generate_invoice_number(clinic_id, payload.date)
        inv = await self.repo.create_invoice(clinic_id, payload, actor, inv_number)

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=patient.id,
                clinic_id=clinic_id,
                event_type="INVOICE_GENERATED",
                title=f"Invoice #{inv_number} Generated",
                description=(
                    f"Grand Total: ₹{inv.grand_total:,.2f}. "
                    f"{len(payload.items)} item(s) billed by Dr. {dentist.first_name} {dentist.last_name}."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="INVOICE",
                entity_id=str(inv.id),
                metadata_json=json.dumps(
                    {
                        "invoice_number": inv_number,
                        "patient_id": str(patient.id),
                        "grand_total": float(inv.grand_total),
                        "items_count": len(payload.items),
                    }
                ),
            )
        )

        await self.db.commit()

        loaded_inv = await self.repo.get_invoice_by_id(clinic_id, inv.id)
        if not loaded_inv:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load created invoice.",
            )
        return self.repo.to_invoice_detail(loaded_inv)

    async def generate_from_treatment(
        self,
        clinic_id: UUID,
        treatment_id: UUID,
        payload: InvoiceGenerateFromTreatment,
        actor: User,
    ) -> InvoiceDetail:
        # Load treatment with procedures
        trt_q = (
            select(Treatment)
            .where(
                Treatment.id == treatment_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
            .options(selectinload(Treatment.procedures))
        )
        res = await self.db.execute(trt_q)
        treatment = res.scalar_one_or_none()
        if not treatment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment record not found in this clinic.",
            )

        inv_number = await self.repo.generate_invoice_number(clinic_id)
        inv = await self.repo.create_invoice_from_treatment(
            clinic_id, treatment, payload, actor, inv_number
        )

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=treatment.patient_id,
                clinic_id=clinic_id,
                event_type="INVOICE_GENERATED",
                title=f"Invoice #{inv_number} Generated from Treatment",
                description=(
                    f"Treatment #{treatment.treatment_number}. "
                    f"Grand Total: ₹{inv.grand_total:,.2f}."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="GENERATE_FROM_TREATMENT",
                entity_type="INVOICE",
                entity_id=str(inv.id),
                metadata_json=json.dumps(
                    {
                        "invoice_number": inv_number,
                        "treatment_id": str(treatment.id),
                        "treatment_number": treatment.treatment_number,
                        "grand_total": float(inv.grand_total),
                    }
                ),
            )
        )

        await self.db.commit()

        loaded_inv = await self.repo.get_invoice_by_id(clinic_id, inv.id)
        if not loaded_inv:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load generated invoice.",
            )
        return self.repo.to_invoice_detail(loaded_inv)

    async def get_invoice(
        self, clinic_id: UUID, invoice_id: UUID
    ) -> InvoiceDetail:
        inv = await self.repo.get_invoice_by_id(clinic_id, invoice_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found in this clinic.",
            )
        return self.repo.to_invoice_detail(inv)

    async def list_invoices(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        treatment_id: UUID | None = None,
        dentist_id: UUID | None = None,
        status_filter: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InvoiceDetail]:
        invoices = await self.repo.list_invoices(
            clinic_id=clinic_id,
            patient_id=patient_id,
            treatment_id=treatment_id,
            dentist_id=dentist_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            search=search,
            limit=limit,
            offset=offset,
        )
        return [self.repo.to_invoice_detail(i) for i in invoices]

    async def update_invoice(
        self,
        clinic_id: UUID,
        invoice_id: UUID,
        payload: InvoiceUpdate,
        actor: User,
    ) -> InvoiceDetail:
        inv = await self.repo.get_invoice_by_id(clinic_id, invoice_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found in this clinic.",
            )

        # Clinical/Financial Invariant: Paid invoices are immutable
        if inv.status == InvoiceStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paid invoices are permanently locked and cannot be edited.",
            )
        if inv.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled invoices cannot be edited.",
            )

        updated_inv = await self.repo.update_invoice(
            clinic_id, inv, payload, actor
        )

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="INVOICE",
                entity_id=str(inv.id),
                metadata_json=json.dumps(
                    {
                        "invoice_number": inv.invoice_number,
                        "grand_total": float(updated_inv.grand_total),
                        "balance_due": float(updated_inv.balance_due),
                    }
                ),
            )
        )

        await self.db.commit()

        reloaded = await self.repo.get_invoice_by_id(clinic_id, inv.id)
        if not reloaded:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load updated invoice.",
            )
        return self.repo.to_invoice_detail(reloaded)

    async def cancel_invoice(
        self,
        clinic_id: UUID,
        invoice_id: UUID,
        payload: InvoiceCancel,
        actor: User,
    ) -> InvoiceDetail:
        inv = await self.repo.get_invoice_by_id(clinic_id, invoice_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found in this clinic.",
            )

        if inv.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already cancelled.",
            )

        if inv.amount_paid > 0.00:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an invoice with recorded payments. Please refund all payments first.",
            )

        cancelled_inv = await self.repo.cancel_invoice(
            clinic_id, inv, payload.reason, actor
        )

        self.db.add(
            PatientTimelineEvent(
                patient_id=inv.patient_id,
                clinic_id=clinic_id,
                event_type="INVOICE_CANCELLED",
                title=f"Invoice #{inv.invoice_number} Cancelled",
                description=f"Reason: {payload.reason}. Cancelled by {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CANCEL",
                entity_type="INVOICE",
                entity_id=str(inv.id),
                metadata_json=json.dumps(
                    {
                        "invoice_number": inv.invoice_number,
                        "reason": payload.reason,
                    }
                ),
            )
        )

        await self.db.commit()
        return self.repo.to_invoice_detail(cancelled_inv)

    async def record_payment(
        self,
        clinic_id: UUID,
        invoice_id: UUID,
        payload: PaymentCreate,
        actor: User,
    ) -> PaymentDetail:
        inv = await self.repo.get_invoice_by_id(clinic_id, invoice_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found in this clinic.",
            )

        if inv.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot record payment for a cancelled invoice.",
            )

        if inv.status == InvoiceStatus.PAID and inv.balance_due <= 0.00:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already fully paid.",
            )

        if payload.amount > inv.balance_due:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount (₹{payload.amount:,.2f}) exceeds outstanding balance (₹{inv.balance_due:,.2f}).",
            )

        receipt_number = await self.repo.generate_receipt_number(
            clinic_id, payload.payment_date
        )
        payment = await self.repo.create_payment(
            clinic_id, inv, payload, actor, receipt_number
        )

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=inv.patient_id,
                clinic_id=clinic_id,
                event_type="PAYMENT_RECEIVED",
                title=f"Payment Received: ₹{payload.amount:,.2f}",
                description=(
                    f"Receipt #{receipt_number} for Invoice #{inv.invoice_number}. "
                    f"Method: {payload.method}. Remaining Balance: ₹{inv.balance_due:,.2f}."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="PAYMENT_RECORDED",
                entity_type="PAYMENT",
                entity_id=str(payment.id),
                metadata_json=json.dumps(
                    {
                        "receipt_number": receipt_number,
                        "invoice_number": inv.invoice_number,
                        "amount": float(payload.amount),
                        "method": payload.method,
                        "remaining_balance": float(inv.balance_due),
                    }
                ),
            )
        )

        await self.db.commit()

        loaded_pay = await self.repo.get_payment_by_id(clinic_id, payment.id)
        if not loaded_pay:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load recorded payment.",
            )
        return self.repo.to_payment_detail(loaded_pay, inv)

    async def refund_payment(
        self,
        clinic_id: UUID,
        payment_id: UUID,
        payload: PaymentRefund,
        actor: User,
    ) -> PaymentDetail:
        payment = await self.repo.get_payment_by_id(clinic_id, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found in this clinic.",
            )

        if payment.status == PaymentStatus.REFUNDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already been refunded.",
            )

        if payload.refund_amount > float(payment.amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund amount (₹{payload.refund_amount:,.2f}) cannot exceed original payment amount (₹{payment.amount:,.2f}).",
            )

        inv = await self.repo.get_invoice_by_id(clinic_id, payment.invoice_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linked invoice not found.",
            )

        refunded_payment = await self.repo.refund_payment(
            clinic_id,
            payment,
            inv,
            payload.refund_amount,
            payload.refund_reason,
            actor,
        )

        # Timeline Event
        self.db.add(
            PatientTimelineEvent(
                patient_id=inv.patient_id,
                clinic_id=clinic_id,
                event_type="PAYMENT_REFUNDED",
                title=f"Payment Refunded: ₹{payload.refund_amount:,.2f}",
                description=(
                    f"Receipt #{payment.receipt_number} refunded. "
                    f"Reason: {payload.refund_reason}. Invoice #{inv.invoice_number} balance adjusted."
                ),
                actor_id=actor.id,
            )
        )

        # Audit Event
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="PAYMENT_REFUNDED",
                entity_type="PAYMENT",
                entity_id=str(payment.id),
                metadata_json=json.dumps(
                    {
                        "receipt_number": payment.receipt_number,
                        "invoice_number": inv.invoice_number,
                        "refund_amount": float(payload.refund_amount),
                        "reason": payload.refund_reason,
                        "new_balance": float(inv.balance_due),
                    }
                ),
            )
        )

        await self.db.commit()
        return self.repo.to_payment_detail(refunded_payment, inv)

    async def get_payment(
        self, clinic_id: UUID, payment_id: UUID
    ) -> PaymentDetail:
        pay = await self.repo.get_payment_by_id(clinic_id, payment_id)
        if not pay:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found in this clinic.",
            )
        return self.repo.to_payment_detail(pay)

    async def get_patient_billing_summary(
        self, clinic_id: UUID, patient_id: UUID
    ) -> PatientBillingSummary:
        patient_q = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        res = await self.db.execute(patient_q)
        patient = res.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found in this clinic.",
            )

        invoices = await self.repo.list_invoices(
            clinic_id=clinic_id, patient_id=patient_id, limit=200
        )
        payments = await self.repo.list_payments_by_patient(
            clinic_id=clinic_id, patient_id=patient_id
        )

        total_invoiced = sum(
            inv.grand_total for inv in invoices if inv.status != InvoiceStatus.CANCELLED
        )
        total_paid = sum(
            p.amount for p in payments if p.status == PaymentStatus.COMPLETED
        )
        balance = max(0.00, round(total_invoiced - total_paid, 2))

        return PatientBillingSummary(
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            patient_number=patient.patient_number,
            total_invoiced=round(total_invoiced, 2),
            total_paid=round(total_paid, 2),
            balance_due=balance,
            invoices_count=len(invoices),
            payments_count=len(payments),
            invoices=[self.repo.to_invoice_detail(i) for i in invoices],
            payments=[self.repo.to_payment_detail(p) for p in payments],
        )

    async def get_dashboard_stats(
        self, clinic_id: UUID
    ) -> BillingDashboardStats:
        return await self.repo.get_dashboard_stats(clinic_id)

    async def get_revenue_report(
        self,
        clinic_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> RevenueReport:
        return await self.repo.get_revenue_report(clinic_id, date_from, date_to)
