from __future__ import annotations

from datetime import date, datetime, time
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
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.patient import Patient
    from app.models.treatment import Treatment


class AppointmentStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_TREATMENT = "IN_TREATMENT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED = "RESCHEDULED"


class VisitType(StrEnum):
    CONSULTATION = "CONSULTATION"
    EMERGENCY = "EMERGENCY"
    FOLLOW_UP = "FOLLOW_UP"
    CLEANING = "CLEANING"
    ROOT_CANAL = "ROOT_CANAL"
    EXTRACTION = "EXTRACTION"
    CROWN = "CROWN"
    IMPLANT = "IMPLANT"
    SURGERY = "SURGERY"
    ORTHODONTICS = "ORTHODONTICS"
    PEDIATRIC = "PEDIATRIC"
    OTHER = "OTHER"


class ChairStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class Chair(Base, UUIDAuditMixin):
    __tablename__ = "chairs"
    __table_args__ = (
        UniqueConstraint("clinic_id", "name", name="uq_chairs_clinic_name"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    room_number: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[ChairStatus] = mapped_column(
        Enum(ChairStatus, name="chair_status"), default=ChairStatus.ACTIVE, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    appointments: Mapped[list[Appointment]] = relationship("Appointment", back_populates="chair")


class DentistWorkingHour(Base, UUIDAuditMixin):
    __tablename__ = "dentist_working_hours"
    __table_args__ = (
        UniqueConstraint("clinic_id", "dentist_id", "day_of_week", name="uq_dentist_working_hour"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    dentist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_start: Mapped[time | None] = mapped_column(Time)
    break_end: Mapped[time | None] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DentistBlockedTime(Base, UUIDAuditMixin):
    __tablename__ = "dentist_blocked_times"

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    dentist_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    block_type: Mapped[str] = mapped_column(String(60), default="LEAVE", nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Appointment(Base, UUIDAuditMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("clinic_id", "appointment_number", name="uq_appointments_clinic_number"),
        Index("ix_appointments_clinic_dentist_date", "clinic_id", "dentist_id", "date"),
        Index("ix_appointments_clinic_chair_date", "clinic_id", "chair_id", "date"),
        Index("ix_appointments_clinic_patient_date", "clinic_id", "patient_id", "date"),
        Index("ix_appointments_clinic_date_status", "clinic_id", "date", "status"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    dentist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    chair_id: Mapped[UUID] = mapped_column(ForeignKey("chairs.id"), index=True, nullable=False)
    appointment_number: Mapped[str] = mapped_column(String(32), nullable=False)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # in minutes

    start_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    visit_type: Mapped[VisitType] = mapped_column(
        Enum(VisitType, name="appointment_visit_type"),
        default=VisitType.CONSULTATION,
        nullable=False,
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    rescheduled_from_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id"))
    is_emergency_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @property
    def reason(self) -> str | None:
        return self.chief_complaint


    # Relationships
    patient: Mapped[Patient] = relationship("Patient", back_populates="appointments")
    dentist: Mapped[User] = relationship("User", foreign_keys=[dentist_id])
    chair: Mapped[Chair] = relationship("Chair", back_populates="appointments")
    timeline_events: Mapped[list[AppointmentTimelineEvent]] = relationship(
        "AppointmentTimelineEvent",
        back_populates="appointment",
        cascade="all, delete-orphan",
        order_by="AppointmentTimelineEvent.created_at.desc()",
    )
    treatment: Mapped[Treatment | None] = relationship(
        "Treatment", back_populates="appointment", uselist=False
    )


class AppointmentTimelineEvent(Base, UUIDAuditMixin):
    __tablename__ = "appointment_timeline_events"
    __table_args__ = (
        Index("ix_apt_timeline_appointment_created", "appointment_id", "created_at"),
    )

    appointment_id: Mapped[UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)

    appointment: Mapped[Appointment] = relationship(
        "Appointment", back_populates="timeline_events"
    )
