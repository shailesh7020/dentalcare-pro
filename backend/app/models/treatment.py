from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
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
    from app.models.billing import Invoice
    from app.models.identity import User
    from app.models.inventory import StockTransaction
    from app.models.patient import Patient
    from app.models.prescription import Prescription


class TreatmentStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"


class FollowUpStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Treatment(Base, UUIDAuditMixin):
    __tablename__ = "treatments"
    __table_args__ = (
        Index("ix_treatments_clinic_patient", "clinic_id", "patient_id"),
        Index("ix_treatments_clinic_date", "clinic_id", "created_at"),
        Index("ix_treatments_clinic_status", "clinic_id", "status"),
        UniqueConstraint("clinic_id", "treatment_number", name="uq_treatments_clinic_number"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    appointment_id: Mapped[UUID] = mapped_column(ForeignKey("appointments.id"), index=True, nullable=False)
    dentist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    treatment_number: Mapped[str] = mapped_column(String(32), nullable=False)

    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    clinical_findings: Mapped[str | None] = mapped_column(Text)
    treatment_plan: Mapped[str | None] = mapped_column(Text)
    procedure_performed: Mapped[str | None] = mapped_column(Text)
    local_anaesthesia_used: Mapped[str | None] = mapped_column(String(255))
    medicines_used: Mapped[str | None] = mapped_column(Text)
    clinical_notes: Mapped[str | None] = mapped_column(Text)

    # Structured SOAP Notes
    soap_subjective: Mapped[str | None] = mapped_column(Text)
    soap_objective: Mapped[str | None] = mapped_column(Text)
    soap_assessment: Mapped[str | None] = mapped_column(Text)
    soap_plan: Mapped[str | None] = mapped_column(Text)

    follow_up_instructions: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TreatmentStatus] = mapped_column(
        Enum(TreatmentStatus, name="treatment_status"),
        default=TreatmentStatus.IN_PROGRESS,
        nullable=False,
    )
    is_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    patient: Mapped[Patient] = relationship("Patient", back_populates="treatments")
    appointment: Mapped[Appointment] = relationship("Appointment", back_populates="treatment")
    dentist: Mapped[User] = relationship("User", foreign_keys=[dentist_id])
    procedures: Mapped[list[TreatmentProcedure]] = relationship(
        "TreatmentProcedure",
        back_populates="treatment",
        cascade="all, delete-orphan",
        order_by="TreatmentProcedure.created_at.asc()",
    )
    follow_ups: Mapped[list[TreatmentFollowUp]] = relationship(
        "TreatmentFollowUp",
        back_populates="treatment",
        cascade="all, delete-orphan",
        order_by="TreatmentFollowUp.follow_up_date.asc()",
    )
    prescriptions: Mapped[list[Prescription]] = relationship(
        "Prescription",
        back_populates="treatment",
        cascade="all, delete-orphan",
        order_by="Prescription.created_at.desc()",
    )
    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice",
        back_populates="treatment",
        order_by="Invoice.created_at.desc()",
    )
    stock_transactions: Mapped[list[StockTransaction]] = relationship(
        "StockTransaction",
        back_populates="treatment",
        order_by="StockTransaction.created_at.desc()",
    )


class TreatmentProcedure(Base, UUIDAuditMixin):
    __tablename__ = "treatment_procedures"

    treatment_id: Mapped[UUID] = mapped_column(
        ForeignKey("treatments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    procedure_name: Mapped[str] = mapped_column(String(160), nullable=False)
    tooth_number: Mapped[str | None] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # minutes
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="COMPLETED", nullable=False)

    treatment: Mapped[Treatment] = relationship("Treatment", back_populates="procedures")


class TreatmentFollowUp(Base, UUIDAuditMixin):
    __tablename__ = "treatment_follow_ups"
    __table_args__ = (
        Index("ix_treatment_followups_clinic_date", "clinic_id", "follow_up_date"),
    )

    treatment_id: Mapped[UUID] = mapped_column(
        ForeignKey("treatments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    follow_up_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus, name="treatment_follow_up_status"),
        default=FollowUpStatus.SCHEDULED,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    treatment: Mapped[Treatment] = relationship("Treatment", back_populates="follow_ups")
    patient: Mapped[Patient] = relationship("Patient")

