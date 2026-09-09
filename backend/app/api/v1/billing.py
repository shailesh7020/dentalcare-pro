from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
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
from app.services.billing_pdf_service import BillingPDFService
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing & Invoicing"])

BILLING_STAFF = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
]
ALL_STAFF = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
]


@router.post(
    "/invoices",
    response_model=InvoiceDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinical invoice",
    description="Creates an invoice for patient care with itemized charges, discounts, and taxes.",
)
async def create_invoice(
    payload: InvoiceCreate,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.create_invoice(actor.clinic_id, payload, actor)


@router.post(
    "/invoices/generate-from-treatment/{treatment_id}",
    response_model=InvoiceDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Generate invoice from completed treatment",
    description="Automatically extracts procedures from a treatment record and generates an itemized invoice.",
)
async def generate_invoice_from_treatment(
    treatment_id: UUID,
    payload: InvoiceGenerateFromTreatment,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.generate_from_treatment(
        actor.clinic_id, treatment_id, payload, actor
    )


@router.get(
    "/dashboard/stats",
    response_model=BillingDashboardStats,
    summary="Billing dashboard metrics",
    description="Returns aggregate revenue, pending collections, outstanding invoices count, and cash vs digital breakdown.",
)
async def get_billing_dashboard_stats(
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> BillingDashboardStats:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.get_dashboard_stats(actor.clinic_id)


@router.get(
    "/reports/revenue",
    response_model=RevenueReport,
    summary="Revenue analytics report",
    description="Returns financial revenue breakdowns across time periods, payment methods, and clinician production.",
)
async def get_revenue_report(
    date_from: date | None = Query(None, description="Start date filter"),
    date_to: date | None = Query(None, description="End date filter"),
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> RevenueReport:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.get_revenue_report(
        actor.clinic_id, date_from=date_from, date_to=date_to
    )


@router.get(
    "/patient/{patient_id}",
    response_model=PatientBillingSummary,
    summary="Patient billing summary",
    description="Returns the patient's complete billing ledger including total billed, total paid, net balance, invoices, and receipts.",
)
async def get_patient_billing_summary(
    patient_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PatientBillingSummary:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.get_patient_billing_summary(actor.clinic_id, patient_id)


@router.get(
    "/treatment/{treatment_id}",
    response_model=list[InvoiceDetail],
    summary="Treatment invoices",
    description="Returns invoices associated with a specific treatment record.",
)
async def get_treatment_invoices(
    treatment_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.list_invoices(
        actor.clinic_id, treatment_id=treatment_id
    )


@router.get(
    "/invoices",
    response_model=list[InvoiceDetail],
    summary="List clinic invoices",
    description="Returns filtered invoices for the clinic with search and status support.",
)
async def list_invoices(
    patient_id: UUID | None = Query(None),
    treatment_id: UUID | None = Query(None),
    dentist_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.list_invoices(
        clinic_id=actor.clinic_id,
        patient_id=patient_id,
        treatment_id=treatment_id,
        dentist_id=dentist_id,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceDetail,
    summary="Get invoice detail",
    description="Retrieves a complete invoice with patient, clinician, line items, and payment history.",
)
async def get_invoice(
    invoice_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.get_invoice(actor.clinic_id, invoice_id)


@router.patch(
    "/invoices/{invoice_id}",
    response_model=InvoiceDetail,
    summary="Update unpaid invoice",
    description="Updates line items, terms, or due date on an unpaid invoice. Fully paid invoices are immutable.",
)
async def update_invoice(
    invoice_id: UUID,
    payload: InvoiceUpdate,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.update_invoice(actor.clinic_id, invoice_id, payload, actor)


@router.post(
    "/invoices/{invoice_id}/cancel",
    response_model=InvoiceDetail,
    summary="Cancel invoice",
    description="Cancels an unpaid invoice with an audited reason.",
)
async def cancel_invoice(
    invoice_id: UUID,
    payload: InvoiceCancel,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> InvoiceDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.cancel_invoice(actor.clinic_id, invoice_id, payload, actor)


@router.get(
    "/invoices/{invoice_id}/pdf",
    summary="Download printable tax invoice PDF",
    description="Generates an official A4 printable dental tax invoice with clinic header and itemized charges.",
)
async def download_invoice_pdf(
    invoice_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    inv = await service.get_invoice(actor.clinic_id, invoice_id)

    pdf_bytes = BillingPDFService.generate_invoice_pdf(inv)
    filename = f"Invoice-{inv.invoice_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.post(
    "/invoices/{invoice_id}/payments",
    response_model=PaymentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Record payment for invoice",
    description="Records a payment, generates an official receipt number, and updates the invoice outstanding balance.",
)
async def record_payment(
    invoice_id: UUID,
    payload: PaymentCreate,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PaymentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.record_payment(
        actor.clinic_id, invoice_id, payload, actor
    )


@router.post(
    "/payments/{payment_id}/refund",
    response_model=PaymentDetail,
    summary="Refund payment",
    description="Issues a full or partial refund on a payment with an audited clinical/financial reason.",
)
async def refund_payment(
    payment_id: UUID,
    payload: PaymentRefund,
    actor: User = Depends(require_roles(*BILLING_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PaymentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.refund_payment(
        actor.clinic_id, payment_id, payload, actor
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentDetail,
    summary="Get payment detail",
    description="Retrieves payment details including method, amount, and remaining invoice balance.",
)
async def get_payment(
    payment_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PaymentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    return await service.get_payment(actor.clinic_id, payment_id)


@router.get(
    "/payments/{payment_id}/pdf",
    summary="Download printable payment receipt PDF",
    description="Generates an official A4 printable payment receipt with payment method, amount, and clinic seal.",
)
async def download_receipt_pdf(
    payment_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = BillingService(db)
    payment = await service.get_payment(actor.clinic_id, payment_id)

    pdf_bytes = BillingPDFService.generate_receipt_pdf(payment)
    filename = f"Receipt-{payment.receipt_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
