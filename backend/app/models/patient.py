from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.billing import Invoice
    from app.models.consent_form import ConsentRecord, PatientForm
    from app.models.odontogram import Tooth, ToothHistory
    from app.models.prescription import Prescription
    from app.models.treatment import Treatment


class Gender(StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    NON_BINARY = "NON_BINARY"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class BloodGroup(StrEnum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "UNKNOWN"


class Patient(Base, UUIDAuditMixin):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("clinic_id", "patient_number", name="uq_patients_clinic_number"),
        Index(
            "uq_patients_clinic_mobile_active",
            "clinic_id",
            "mobile_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_number: Mapped[str] = mapped_column(String(32), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="patient_gender"), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[BloodGroup | None] = mapped_column(
        Enum(BloodGroup, name="blood_group", values_callable=lambda obj: [e.value for e in obj])
    )
    marital_status: Mapped[str | None] = mapped_column(String(40))
    occupation: Mapped[str | None] = mapped_column(String(100))
    aadhaar_number: Mapped[str | None] = mapped_column(String(12), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    mobile_number: Mapped[str] = mapped_column(String(15), nullable=False)
    alternate_mobile: Mapped[str | None] = mapped_column(String(15))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(80), default="India", nullable=False)
    pin_code: Mapped[str | None] = mapped_column(String(6))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(160))
    emergency_contact_number: Mapped[str | None] = mapped_column(String(15))
    emergency_contact_relation: Mapped[str | None] = mapped_column(String(60))
    insurance_provider: Mapped[str | None] = mapped_column(String(160))
    insurance_policy_number: Mapped[str | None] = mapped_column(String(100))
    preferred_language: Mapped[str] = mapped_column(String(40), default="English", nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    medical_history: Mapped[MedicalHistory | None] = relationship(
        "MedicalHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan"
    )
    dental_history: Mapped[DentalHistory | None] = relationship(
        "DentalHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan"
    )
    timeline_events: Mapped[list[PatientTimelineEvent]] = relationship(
        "PatientTimelineEvent", back_populates="patient", cascade="all, delete-orphan"
    )
    documents: Mapped[list[PatientDocument]] = relationship(
        "PatientDocument", back_populates="patient", cascade="all, delete-orphan"
    )
    appointments: Mapped[list[Appointment]] = relationship(
        "Appointment", back_populates="patient", cascade="all, delete-orphan"
    )
    treatments: Mapped[list[Treatment]] = relationship(
        "Treatment", back_populates="patient", cascade="all, delete-orphan"
    )
    teeth: Mapped[list[Tooth]] = relationship(
        "Tooth", back_populates="patient", cascade="all, delete-orphan"
    )
    tooth_history: Mapped[list[ToothHistory]] = relationship(
        "ToothHistory", back_populates="patient", cascade="all, delete-orphan"
    )
    prescriptions: Mapped[list[Prescription]] = relationship(
        "Prescription", back_populates="patient", cascade="all, delete-orphan"
    )
    invoices: Mapped[list[Invoice]] = relationship(
        "Invoice", back_populates="patient", cascade="all, delete-orphan"
    )
    forms: Mapped[list[PatientForm]] = relationship(
        "PatientForm", back_populates="patient", cascade="all, delete-orphan"
    )
    consents: Mapped[list[ConsentRecord]] = relationship(
        "ConsentRecord", back_populates="patient", cascade="all, delete-orphan"
    )

    @property
    def status(self) -> str:
        return "ARCHIVED" if self.deleted_at is not None else "ACTIVE"

    @property
    def age(self) -> int:
        today = datetime.now(UTC).date()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )


class MedicalHistory(Base, UUIDAuditMixin):
    __tablename__ = "medical_histories"
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), unique=True, index=True
    )
    diabetes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hypertension: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cardiac_disease: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thyroid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    asthma: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    epilepsy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pregnancy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allergies: Mapped[str | None] = mapped_column(Text)
    current_medications: Mapped[str | None] = mapped_column(Text)
    smoking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tobacco: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alcohol: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    previous_surgeries: Mapped[str | None] = mapped_column(Text)
    infectious_diseases: Mapped[str | None] = mapped_column(Text)
    physician_name: Mapped[str | None] = mapped_column(String(160))
    physician_contact: Mapped[str | None] = mapped_column(String(15))
    additional_notes: Mapped[str | None] = mapped_column(Text)

    patient: Mapped[Patient] = relationship("Patient", back_populates="medical_history")


class DentalHistory(Base, UUIDAuditMixin):
    __tablename__ = "dental_histories"
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), unique=True, index=True
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    previous_dental_treatments: Mapped[str | None] = mapped_column(Text)
    brushing_frequency: Mapped[str | None] = mapped_column(String(40))
    flossing_habit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tobacco_habit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    grinding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    jaw_pain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tmj_disorder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sensitivity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bleeding_gums: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_dental_visit: Mapped[date | None] = mapped_column(Date)
    dental_notes: Mapped[str | None] = mapped_column(Text)

    patient: Mapped[Patient] = relationship("Patient", back_populates="dental_history")


class PatientTimelineEvent(Base, UUIDAuditMixin):
    __tablename__ = "patient_timeline_events"
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    patient: Mapped[Patient] = relationship("Patient", back_populates="timeline_events")


class PatientDocument(Base, UUIDAuditMixin):
    __tablename__ = "patient_documents"
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(60), nullable=False, default="DOCUMENT")

    patient: Mapped[Patient] = relationship("Patient", back_populates="documents")
