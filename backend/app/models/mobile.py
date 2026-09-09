from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDAuditMixin


class DeviceType(StrEnum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB_PWA = "WEB_PWA"


class SyncType(StrEnum):
    PULL = "PULL"
    PUSH = "PUSH"


class SyncStatus(StrEnum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"
    REJECTED = "REJECTED"


class SignatureType(StrEnum):
    PATIENT_CONSENT = "PATIENT_CONSENT"
    DENTIST_TREATMENT_APPROVAL = "DENTIST_TREATMENT_APPROVAL"
    INSURANCE_AUTHORIZATION = "INSURANCE_AUTHORIZATION"
    PRESCRIPTION_SIGN_OFF = "PRESCRIPTION_SIGN_OFF"


class MobileMediaType(StrEnum):
    INTRAORAL_PHOTO = "INTRAORAL_PHOTO"
    EXTRAORAL_PHOTO = "EXTRAORAL_PHOTO"
    XRAY_PHOTO = "XRAY_PHOTO"
    DOCUMENT_SCAN = "DOCUMENT_SCAN"
    VOICE_NOTE = "VOICE_NOTE"


class MobileDevice(Base, UUIDAuditMixin):
    __tablename__ = "mobile_devices"

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    clinic_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True)
    device_token: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False, default=DeviceType.ANDROID)
    device_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    biometric_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MobileSyncQueue(Base, UUIDAuditMixin):
    __tablename__ = "mobile_sync_queues"

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("mobile_devices.id", ondelete="SET NULL"), nullable=True)
    sync_type: Mapped[str] = mapped_column(String(16), nullable=False, default=SyncType.PUSH)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    client_mutation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SyncStatus.APPLIED)
    client_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    server_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class MobileDigitalSignature(Base, UUIDAuditMixin):
    __tablename__ = "mobile_digital_signatures"

    clinic_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True)
    signer_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    signature_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    signature_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MobileClinicalMedia(Base, UUIDAuditMixin):
    __tablename__ = "mobile_clinical_media"

    clinic_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True)
    patient_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    treatment_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True, index=True)
    captured_by_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    tooth_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    compression_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
