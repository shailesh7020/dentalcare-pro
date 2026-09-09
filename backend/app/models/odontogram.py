from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.patient import Patient


class ToothCondition(StrEnum):
    HEALTHY = "HEALTHY"
    CARIES = "CARIES"
    FILLING = "FILLING"
    ROOT_CANAL = "ROOT_CANAL"
    CROWN = "CROWN"
    IMPLANT = "IMPLANT"
    EXTRACTION = "EXTRACTION"
    MISSING = "MISSING"
    BRIDGE = "BRIDGE"
    OBSERVATION = "OBSERVATION"
    TEMPORARY_CROWN = "TEMPORARY_CROWN"
    TEMPORARY_FILLING = "TEMPORARY_FILLING"
    VENEER = "VENEER"
    FRACTURE = "FRACTURE"
    SEALANT = "SEALANT"
    ORTHODONTIC_BRACKET = "ORTHODONTIC_BRACKET"
    MOBILE_TOOTH = "MOBILE_TOOTH"
    IMPACTED = "IMPACTED"


class ToothSurfaceEnum(StrEnum):
    MESIAL = "MESIAL"
    DISTAL = "DISTAL"
    BUCCAL = "BUCCAL"
    LINGUAL = "LINGUAL"
    OCCLUSAL = "OCCLUSAL"
    INCISAL = "INCISAL"
    CERVICAL = "CERVICAL"
    ROOT = "ROOT"


class DentitionType(StrEnum):
    ADULT = "ADULT"
    PRIMARY = "PRIMARY"


class ToothArch(StrEnum):
    UPPER = "UPPER"
    LOWER = "LOWER"


class ToothType(StrEnum):
    INCISOR = "INCISOR"
    CANINE = "CANINE"
    PREMOLAR = "PREMOLAR"
    MOLAR = "MOLAR"


class NumberingSystem(StrEnum):
    FDI = "FDI"
    UNIVERSAL = "UNIVERSAL"
    PALMER = "PALMER"


COLOR_STANDARDS: dict[str, str] = {
    ToothCondition.HEALTHY: "#10B981",
    ToothCondition.CARIES: "#EF4444",
    ToothCondition.FILLING: "#3B82F6",
    ToothCondition.ROOT_CANAL: "#8B5CF6",
    ToothCondition.CROWN: "#F59E0B",
    ToothCondition.IMPLANT: "#94A3B8",
    ToothCondition.EXTRACTION: "#1E293B",
    ToothCondition.MISSING: "#64748B",
    ToothCondition.BRIDGE: "#854D0E",
    ToothCondition.OBSERVATION: "#EAB308",
    ToothCondition.TEMPORARY_CROWN: "#F97316",
    ToothCondition.TEMPORARY_FILLING: "#F97316",
    ToothCondition.VENEER: "#14B8A6",
    ToothCondition.FRACTURE: "#E11D48",
    ToothCondition.SEALANT: "#06B6D4",
    ToothCondition.ORTHODONTIC_BRACKET: "#6366F1",
    ToothCondition.MOBILE_TOOTH: "#D97706",
    ToothCondition.IMPACTED: "#7C3AED",
}


class Tooth(Base, UUIDAuditMixin):
    __tablename__ = "teeth"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id", "patient_id", "tooth_number", name="uq_teeth_clinic_patient_tooth"
        ),
        Index("ix_teeth_clinic_patient", "clinic_id", "patient_id"),
        Index("ix_teeth_patient_tooth", "patient_id", "tooth_number"),
        Index("ix_teeth_clinic_status", "clinic_id", "primary_status"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    tooth_number: Mapped[str] = mapped_column(String(10), nullable=False)
    universal_number: Mapped[str] = mapped_column(String(10), nullable=False)
    palmer_notation: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    dentition_type: Mapped[str] = mapped_column(String(20), default="ADULT", nullable=False)
    arch: Mapped[str] = mapped_column(String(20), nullable=False)
    quadrant: Mapped[int] = mapped_column(Integer, nullable=False)
    tooth_type: Mapped[str] = mapped_column(String(30), nullable=False)
    primary_status: Mapped[str] = mapped_column(String(40), default="HEALTHY", nullable=False)
    color: Mapped[str] = mapped_column(String(30), default="#10B981", nullable=False)

    is_missing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_impacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_root_canal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_crown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_implant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_bridge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mobility_grade: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    patient: Mapped[Patient] = relationship("Patient", back_populates="teeth")
    surfaces: Mapped[list[ToothSurface]] = relationship(
        "ToothSurface",
        back_populates="tooth",
        cascade="all, delete-orphan",
        order_by="ToothSurface.surface.asc()",
    )
    history: Mapped[list[ToothHistory]] = relationship(
        "ToothHistory",
        back_populates="tooth",
        cascade="all, delete-orphan",
        order_by="ToothHistory.created_at.desc()",
    )


class ToothSurface(Base, UUIDAuditMixin):
    __tablename__ = "tooth_surfaces"
    __table_args__ = (
        UniqueConstraint("tooth_id", "surface", name="uq_tooth_surfaces_tooth_surface"),
        Index("ix_tooth_surfaces_tooth_id", "tooth_id"),
        Index("ix_tooth_surfaces_clinic", "clinic_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    tooth_id: Mapped[UUID] = mapped_column(ForeignKey("teeth.id", ondelete="CASCADE"), nullable=False)
    surface: Mapped[str] = mapped_column(String(20), nullable=False)
    condition: Mapped[str] = mapped_column(String(60), default="HEALTHY", nullable=False)
    treatment: Mapped[str] = mapped_column(String(60), default="NONE", nullable=False)
    color: Mapped[str] = mapped_column(String(30), default="#10B981", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    dentist_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    tooth: Mapped[Tooth] = relationship("Tooth", back_populates="surfaces")
    dentist: Mapped[User | None] = relationship("User", foreign_keys=[dentist_id])


class ToothHistory(Base):
    __tablename__ = "tooth_history"
    __table_args__ = (
        Index("ix_tooth_history_patient", "clinic_id", "patient_id"),
        Index("ix_tooth_history_tooth", "clinic_id", "tooth_id"),
        Index("ix_tooth_history_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    tooth_id: Mapped[UUID] = mapped_column(ForeignKey("teeth.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    previous_state: Mapped[str | None] = mapped_column(Text)
    new_state: Mapped[str | None] = mapped_column(Text)
    affected_surfaces: Mapped[str | None] = mapped_column(String(100))
    treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True)
    treatment_procedure_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_procedures.id", ondelete="SET NULL"), nullable=True
    )
    appointment_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    dentist_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    tooth: Mapped[Tooth] = relationship("Tooth", back_populates="history")
    patient: Mapped[Patient] = relationship("Patient", back_populates="tooth_history")
    dentist: Mapped[User | None] = relationship("User", foreign_keys=[dentist_id])
