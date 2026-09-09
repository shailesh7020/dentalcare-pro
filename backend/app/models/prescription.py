from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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


class PrescriptionStatus(StrEnum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    MODIFIED = "MODIFIED"
    CANCELLED = "CANCELLED"


class MedicineForm(StrEnum):
    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    SYRUP = "SYRUP"
    INJECTION = "INJECTION"
    GEL = "GEL"
    CREAM = "CREAM"
    MOUTHWASH = "MOUTHWASH"
    DENTAL_PASTE = "DENTAL_PASTE"
    POWDER = "POWDER"
    OTHER = "OTHER"


class DosageFrequency(StrEnum):
    OD = "OD"  # Once daily (Omni Die)
    BD = "BD"  # Twice daily (Bis Die)
    TDS = "TDS"  # Thrice daily (Ter Die Sumendum)
    QID = "QID"  # Four times daily (Quater In Die)
    SOS = "SOS"  # As needed (Si Opus Sit)
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class AdministrationRoute(StrEnum):
    ORAL = "Oral"
    SUBLINGUAL = "Sublingual"
    TOPICAL = "Topical"
    INFILTRATION = "Infiltration"
    INTRAMUSCULAR = "Intramuscular"
    SUBCUTANEOUS = "Subcutaneous"
    OTHER = "Other"


class TemplateCategory(StrEnum):
    EXTRACTION = "EXTRACTION"
    ROOT_CANAL = "ROOT_CANAL"
    IMPLANT = "IMPLANT"
    SCALING = "SCALING"
    SURGERY = "SURGERY"
    PEDIATRIC = "PEDIATRIC"
    EMERGENCY = "EMERGENCY"
    GENERAL = "GENERAL"


class MedicineCatalog(Base, UUIDAuditMixin):
    __tablename__ = "medicine_catalog"
    __table_args__ = (
        Index("ix_medicine_catalog_generic", "generic_name"),
        Index("ix_medicine_catalog_brand", "brand_name"),
        Index("ix_medicine_catalog_clinic", "clinic_id"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    generic_name: Mapped[str] = mapped_column(String(160), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(160), nullable=False)
    strength: Mapped[str] = mapped_column(String(80), nullable=False)
    form: Mapped[str] = mapped_column(String(50), default=MedicineForm.TABLET, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    standard_dosage: Mapped[str | None] = mapped_column(String(120))
    default_route: Mapped[str] = mapped_column(String(50), default="Oral", nullable=False)
    default_frequency: Mapped[str] = mapped_column(String(30), default="BD", nullable=False)
    default_duration: Mapped[str] = mapped_column(String(50), default="5 days", nullable=False)
    default_instructions: Mapped[str | None] = mapped_column(String(255), default="After food")
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PrescriptionTemplate(Base, UUIDAuditMixin):
    __tablename__ = "prescription_templates"
    __table_args__ = (
        Index("ix_prescription_templates_clinic", "clinic_id"),
        Index("ix_prescription_templates_category", "category"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default=TemplateCategory.GENERAL, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    diagnosis_template: Mapped[str | None] = mapped_column(Text)
    instructions_template: Mapped[str | None] = mapped_column(Text)
    default_items: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Prescription(Base, UUIDAuditMixin):
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index("ix_prescriptions_clinic_patient", "clinic_id", "patient_id"),
        Index("ix_prescriptions_clinic_treatment", "clinic_id", "treatment_id"),
        Index("ix_prescriptions_clinic_appointment", "clinic_id", "appointment_id"),
        Index("ix_prescriptions_clinic_status", "clinic_id", "status"),
        Index("ix_prescriptions_clinic_date", "clinic_id", "date"),
        UniqueConstraint("clinic_id", "prescription_number", name="uq_prescriptions_clinic_number"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    treatment_id: Mapped[UUID] = mapped_column(ForeignKey("treatments.id"), index=True, nullable=False)
    appointment_id: Mapped[UUID] = mapped_column(ForeignKey("appointments.id"), index=True, nullable=False)
    dentist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    prescription_number: Mapped[str] = mapped_column(String(32), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(30), default=PrescriptionStatus.DRAFT, nullable=False
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    clinic: Mapped[Clinic] = relationship("Clinic", lazy="select")
    patient: Mapped[Patient] = relationship("Patient", back_populates="prescriptions", lazy="select")
    treatment: Mapped[Treatment] = relationship("Treatment", back_populates="prescriptions", lazy="select")
    appointment: Mapped[Appointment] = relationship("Appointment", lazy="select")
    dentist: Mapped[User] = relationship("User", lazy="select")
    items: Mapped[list[PrescriptionItem]] = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
        order_by="PrescriptionItem.created_at",
        lazy="selectin",
    )


class PrescriptionItem(Base, UUIDAuditMixin):
    __tablename__ = "prescription_items"
    __table_args__ = (
        Index("ix_prescription_items_prescription_id", "prescription_id"),
    )

    prescription_id: Mapped[UUID] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    medicine_name: Mapped[str] = mapped_column(String(160), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(160))
    brand_name: Mapped[str | None] = mapped_column(String(160))
    strength: Mapped[str] = mapped_column(String(80), nullable=False)
    form: Mapped[str] = mapped_column(String(50), default=MedicineForm.TABLET, nullable=False)
    dosage: Mapped[str] = mapped_column(String(80), nullable=False)
    route: Mapped[str] = mapped_column(String(50), default="Oral", nullable=False)
    frequency: Mapped[str] = mapped_column(String(30), nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    timing: Mapped[str | None] = mapped_column(String(100))
    food_instructions: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    prescription: Mapped[Prescription] = relationship("Prescription", back_populates="items")
