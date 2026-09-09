from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.identity import Clinic, User
    from app.models.patient import Patient
    from app.models.treatment import Treatment


class InvoiceStatus(StrEnum):
    DRAFT = "DRAFT"
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class InvoiceItemType(StrEnum):
    CONSULTATION = "CONSULTATION"
    PROCEDURE = "PROCEDURE"
    MEDICINE = "MEDICINE"
    LABORATORY = "LABORATORY"
    X_RAY = "X_RAY"
    MISCELLANEOUS = "MISCELLANEOUS"


class PaymentMethod(StrEnum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    WALLET = "WALLET"
    MIXED = "MIXED"
    INSURANCE = "INSURANCE"


class DiscountType(StrEnum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class PaymentStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"


class Invoice(Base, UUIDAuditMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_clinic_patient", "clinic_id", "patient_id"),
        Index("ix_invoices_clinic_date", "clinic_id", "date"),
        Index("ix_invoices_clinic_status", "clinic_id", "status"),
        UniqueConstraint("clinic_id", "invoice_number", name="uq_invoices_clinic_number"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    appointment_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id"), index=True)
    treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id"), index=True)
    dentist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    invoice_number: Mapped[str] = mapped_column(String(32), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.UNPAID,
        nullable=False,
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type"),
        default=DiscountType.FIXED,
        nullable=False,
    )
    discount_value: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    grand_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    balance_due: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    clinic: Mapped[Clinic] = relationship("Clinic")
    patient: Mapped[Patient] = relationship("Patient", back_populates="invoices")
    appointment: Mapped[Appointment | None] = relationship("Appointment")
    treatment: Mapped[Treatment | None] = relationship("Treatment", back_populates="invoices")
    dentist: Mapped[User] = relationship("User", foreign_keys=[dentist_id])
    items: Mapped[list[InvoiceItem]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.created_at.asc()",
    )
    payments: Mapped[list[Payment]] = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Payment.payment_date.asc()",
    )


class InvoiceItem(Base, UUIDAuditMixin):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False
    )
    item_type: Mapped[InvoiceItemType] = mapped_column(
        Enum(InvoiceItemType, name="invoice_item_type"),
        default=InvoiceItemType.PROCEDURE,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    procedure_id: Mapped[UUID | None] = mapped_column(nullable=True)

    # Relationships
    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="items")


class Payment(Base, UUIDAuditMixin):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_clinic_date", "clinic_id", "payment_date"),
        UniqueConstraint("clinic_id", "receipt_number", name="uq_payments_clinic_receipt"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=False)

    receipt_number: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        default=PaymentMethod.CASH,
        nullable=False,
    )
    transaction_reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    received_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.COMPLETED,
        nullable=False,
    )
    refund_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    refund_reason: Mapped[str | None] = mapped_column(Text)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="payments")
    receiver: Mapped[User] = relationship("User", foreign_keys=[received_by])
    clinic: Mapped[Clinic] = relationship("Clinic")
