from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.billing import (
    DiscountType,
    InvoiceItemType,
    InvoiceStatus,
    PaymentMethod,
    PaymentStatus,
)


# ==========================================
# Invoice Item Schemas
# ==========================================
class InvoiceItemBase(BaseModel):
    item_type: InvoiceItemType = Field(default=InvoiceItemType.PROCEDURE)
    description: str = Field(min_length=1, max_length=255)
    quantity: int = Field(default=1, ge=1, le=500)
    unit_price: float = Field(default=0.00, ge=0.0)
    discount_amount: float = Field(default=0.00, ge=0.0)
    tax_rate: float = Field(default=0.00, ge=0.0, le=100.0)
    tax_amount: float = Field(default=0.00, ge=0.0)
    procedure_id: UUID | None = None


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    total: float
    created_at: datetime
    updated_at: datetime


# ==========================================
# Payment Schemas
# ==========================================
class PaymentBase(BaseModel):
    payment_date: dt_date | None = None
    amount: float = Field(gt=0.0, description="Payment amount received")
    method: PaymentMethod = Field(default=PaymentMethod.CASH)
    transaction_reference: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)


class PaymentCreate(PaymentBase):
    pass


class PaymentRefund(BaseModel):
    refund_amount: float = Field(gt=0.0, description="Amount to refund")
    refund_reason: str = Field(min_length=3, max_length=1000, description="Clinical/financial reason for refund")


class PaymentRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    invoice_id: UUID
    receipt_number: str
    received_by: UUID
    status: PaymentStatus
    refund_amount: float = 0.00
    refund_reason: str | None = None
    refunded_at: datetime | None = None
    refunded_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class PaymentDetail(PaymentRead):
    receiver_name: str | None = None
    invoice_number: str | None = None
    patient_name: str | None = None
    patient_number: str | None = None
    clinic_name: str | None = None
    clinic_phone: str | None = None
    clinic_email: str | None = None
    remaining_balance: float = 0.00


# ==========================================
# Invoice Schemas
# ==========================================
class InvoiceBase(BaseModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    treatment_id: UUID | None = None
    dentist_id: UUID
    date: dt_date | None = None
    due_date: dt_date | None = None
    discount_type: DiscountType = Field(default=DiscountType.FIXED)
    discount_value: float = Field(default=0.00, ge=0.0)
    tax_rate: float = Field(default=0.00, ge=0.0, le=100.0)
    notes: str | None = Field(None, max_length=2000)
    terms: str | None = Field(None, max_length=2000)


class InvoiceCreate(InvoiceBase):
    items: list[InvoiceItemCreate] = Field(min_length=1, description="Line items for the invoice")


class InvoiceGenerateFromTreatment(BaseModel):
    consultation_fee: float = Field(default=0.00, ge=0.0)
    discount_type: DiscountType = Field(default=DiscountType.FIXED)
    discount_value: float = Field(default=0.00, ge=0.0)
    tax_rate: float = Field(default=0.00, ge=0.0, le=100.0)
    notes: str | None = None
    terms: str | None = None
    due_date: dt_date | None = None


class InvoiceUpdate(BaseModel):
    due_date: dt_date | None = None
    discount_type: DiscountType | None = None
    discount_value: float | None = Field(None, ge=0.0)
    tax_rate: float | None = Field(None, ge=0.0, le=100.0)
    notes: str | None = None
    terms: str | None = None
    items: list[InvoiceItemCreate] | None = None


class InvoiceCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=1000, description="Cancellation reason")


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    invoice_number: str
    status: InvoiceStatus
    subtotal: float
    discount_amount: float
    tax_amount: float
    grand_total: float
    amount_paid: float
    balance_due: float
    cancellation_reason: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class InvoiceDetail(InvoiceRead):
    items: list[InvoiceItemRead] = []
    payments: list[PaymentRead] = []
    patient_name: str | None = None
    patient_number: str | None = None
    patient_phone: str | None = None
    patient_email: str | None = None
    dentist_name: str | None = None
    treatment_number: str | None = None
    appointment_number: str | None = None
    clinic_name: str | None = None
    clinic_phone: str | None = None
    clinic_email: str | None = None
    clinic_address: str | None = None


# ==========================================
# Reporting & Statistics Schemas
# ==========================================
class BillingDashboardStats(BaseModel):
    total_revenue: float
    today_revenue: float
    monthly_revenue: float
    pending_payments: float
    outstanding_invoices_count: int
    paid_invoices_count: int
    total_invoices_count: int
    cash_collections: float
    digital_collections: float


class RevenueReportItem(BaseModel):
    period: str  # e.g. "2026-09" or "2026-09-08"
    total_invoiced: float
    total_collected: float
    balance_outstanding: float
    invoices_count: int


class RevenueReport(BaseModel):
    items: list[RevenueReportItem]
    total_invoiced: float
    total_collected: float
    total_outstanding: float
    collections_by_method: dict[str, float]
    dentist_revenue: dict[str, float]


class PatientBillingSummary(BaseModel):
    patient_id: UUID
    patient_name: str
    patient_number: str
    total_invoiced: float
    total_paid: float
    balance_due: float
    invoices_count: int
    payments_count: int
    invoices: list[InvoiceDetail] = []
    payments: list[PaymentDetail] = []
