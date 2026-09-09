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
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import Clinic, User
    from app.models.patient import Patient
    from app.models.treatment import Treatment


class FormType(StrEnum):
    REGISTRATION = "REGISTRATION"
    MEDICAL_HISTORY = "MEDICAL_HISTORY"
    TREATMENT_CONSENT = "TREATMENT_CONSENT"
    SURGICAL_CONSENT = "SURGICAL_CONSENT"
    IMPLANT_CONSENT = "IMPLANT_CONSENT"
    ORTHODONTIC_CONSENT = "ORTHODONTIC_CONSENT"
    FEEDBACK = "FEEDBACK"
    CUSTOM = "CUSTOM"


class FormStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"



class FormTemplate(Base, UUIDAuditMixin):
    __tablename__ = "form_templates"
    __table_args__ = (
        Index("ix_form_templates_clinic_id", "clinic_id"),
        Index("ix_form_templates_type", "clinic_id", "form_type"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    form_type: Mapped[FormType] = mapped_column(
        Enum(FormType, name="form_type"), default=FormType.CUSTOM, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    schema_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic | None] = relationship("Clinic")
    submissions: Mapped[list[PatientForm]] = relationship("PatientForm", back_populates="template")


class PatientForm(Base, UUIDAuditMixin):
    __tablename__ = "patient_forms"
    __table_args__ = (
        Index("ix_patient_forms_clinic_id", "clinic_id"),
        Index("ix_patient_forms_patient_id", "patient_id"),
        Index("ix_patient_forms_status", "clinic_id", "status"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("form_templates.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[FormStatus] = mapped_column(
        Enum(FormStatus, name="patient_form_status"),
        default=FormStatus.DRAFT,
        nullable=False,
    )
    answers_json: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    clinic: Mapped[Clinic] = relationship("Clinic")
    patient: Mapped[Patient] = relationship("Patient", back_populates="forms")
    template: Mapped[FormTemplate] = relationship("FormTemplate", back_populates="submissions")
    reviewed_by: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by_id])


class ConsentRecord(Base, UUIDAuditMixin):
    __tablename__ = "consent_records"
    __table_args__ = (
        Index("ix_consent_records_clinic_id", "clinic_id"),
        Index("ix_consent_records_patient_id", "patient_id"),
        Index("ix_consent_records_treatment_id", "treatment_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    treatment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True
    )
    consent_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    patient_signature: Mapped[str] = mapped_column(Text, nullable=False)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    witness_name: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[date | None] = mapped_column(Date)

    clinic: Mapped[Clinic] = relationship("Clinic")
    patient: Mapped[Patient] = relationship("Patient", back_populates="consents")
    treatment: Mapped[Treatment | None] = relationship("Treatment")
