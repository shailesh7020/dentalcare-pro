from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
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


class AIProviderType(StrEnum):
    MOCK = "MOCK"
    OLLAMA = "OLLAMA"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    AZURE_OPENAI = "AZURE_OPENAI"


class AITaskType(StrEnum):
    PATIENT_SUMMARY = "PATIENT_SUMMARY"
    SOAP_NOTE = "SOAP_NOTE"
    PRESCRIPTION_ASSISTANCE = "PRESCRIPTION_ASSISTANCE"
    TREATMENT_PLAN = "TREATMENT_PLAN"
    DOCUMENTATION = "DOCUMENTATION"
    BILLING_AUDIT = "BILLING_AUDIT"
    SCHEDULING = "SCHEDULING"
    INVENTORY_FORECAST = "INVENTORY_FORECAST"
    BUSINESS_ANALYTICS = "BUSINESS_ANALYTICS"
    NATURAL_LANGUAGE_SEARCH = "NATURAL_LANGUAGE_SEARCH"


class AIRecommendationStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    EDITED_AND_APPROVED = "EDITED_AND_APPROVED"
    REJECTED = "REJECTED"


class AIConfiguration(Base, UUIDAuditMixin):
    __tablename__ = "ai_configurations"
    __table_args__ = (
        Index("ix_ai_configurations_clinic", "clinic_id"),
        UniqueConstraint("clinic_id", name="uq_ai_configurations_clinic"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    provider_type: Mapped[str] = mapped_column(
        String(40), default=AIProviderType.MOCK, nullable=False
    )
    model_name: Mapped[str] = mapped_column(
        String(120), default="mock-dental-llm", nullable=False
    )
    api_base_url: Mapped[str | None] = mapped_column(String(255))
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    clinical_guardrails_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic] = relationship("Clinic")


class AIPromptTemplate(Base, UUIDAuditMixin):
    __tablename__ = "ai_prompt_templates"
    __table_args__ = (
        Index("ix_ai_prompt_templates_clinic", "clinic_id"),
        Index("ix_ai_prompt_templates_key", "template_key"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
    )
    template_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    clinic: Mapped[Clinic | None] = relationship("Clinic")


class AIAuditLog(Base, UUIDAuditMixin):
    __tablename__ = "ai_audit_logs"
    __table_args__ = (
        Index("ix_ai_audit_logs_clinic", "clinic_id"),
        Index("ix_ai_audit_logs_task", "task_type"),
        Index("ix_ai_audit_logs_req", "request_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(60), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anonymized_prompt_summary: Mapped[str | None] = mapped_column(Text)
    response_summary: Mapped[str | None] = mapped_column(Text)
    safety_flags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False)

    clinic: Mapped[Clinic] = relationship("Clinic")
    user: Mapped[User | None] = relationship("User")
    patient: Mapped[Patient | None] = relationship("Patient")


class AIRecommendation(Base, UUIDAuditMixin):
    __tablename__ = "ai_recommendations"
    __table_args__ = (
        Index("ix_ai_recommendations_clinic", "clinic_id"),
        Index("ix_ai_recommendations_patient", "patient_id"),
        Index("ix_ai_recommendations_status", "status"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    dentist_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    appointment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )
    treatment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True
    )
    recommendation_type: Mapped[str] = mapped_column(String(60), nullable=False)
    input_context_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    generated_output_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(40), default=AIRecommendationStatus.PENDING_REVIEW, nullable=False
    )
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clinician_feedback: Mapped[str | None] = mapped_column(Text)
    final_content: Mapped[str | None] = mapped_column(Text)

    clinic: Mapped[Clinic] = relationship("Clinic")
    patient: Mapped[Patient] = relationship("Patient")
    dentist: Mapped[User] = relationship("User", foreign_keys=[dentist_id])
    reviewer: Mapped[User | None] = relationship("User", foreign_keys=[reviewed_by_id])
    appointment: Mapped[Appointment | None] = relationship("Appointment")
    treatment: Mapped[Treatment | None] = relationship("Treatment")
