from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.mobile import (
    DeviceType,
    MobileMediaType,
    SignatureType,
    SyncStatus,
)


class MobileDeviceRegister(BaseModel):
    device_token: str = Field(..., min_length=1, max_length=512)
    device_type: DeviceType = DeviceType.ANDROID
    device_name: str | None = Field(default=None, max_length=128)
    device_os_version: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=32)
    biometric_enabled: bool = False


class MobileDeviceUpdate(BaseModel):
    device_name: str | None = None
    app_version: str | None = None
    biometric_enabled: bool | None = None


class MobileDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    clinic_id: UUID | None = None
    device_token: str
    device_type: str
    device_name: str | None = None
    device_os_version: str | None = None
    app_version: str | None = None
    is_active: bool
    last_active_at: datetime | None = None
    biometric_enabled: bool
    created_at: datetime


class MobileMutation(BaseModel):
    client_mutation_id: str
    entity_type: str
    action: str = Field(default="CREATE", description="CREATE, UPDATE, DELETE")
    entity_id: UUID | None = None
    client_timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class MobileSyncPushRequest(BaseModel):
    device_id: UUID | None = None
    mutations: list[MobileMutation] = Field(default_factory=list)


class MobileSyncMutationResult(BaseModel):
    client_mutation_id: str
    entity_type: str
    entity_id: UUID | None = None
    status: SyncStatus
    conflict_resolved: bool = False
    message: str | None = None


class MobileSyncPushResponse(BaseModel):
    processed_count: int
    success_count: int
    conflict_count: int
    results: list[MobileSyncMutationResult]
    server_timestamp: datetime


class MobileSyncPullResponse(BaseModel):
    server_timestamp: datetime
    appointments: list[dict[str, Any]] = Field(default_factory=list)
    patients: list[dict[str, Any]] = Field(default_factory=list)
    treatments: list[dict[str, Any]] = Field(default_factory=list)
    prescriptions: list[dict[str, Any]] = Field(default_factory=list)
    invoices: list[dict[str, Any]] = Field(default_factory=list)
    notifications: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool = False


class MobileDigitalSignatureCreate(BaseModel):
    signature_type: SignatureType
    target_entity_type: str
    target_entity_id: UUID
    patient_id: UUID | None = None
    signature_image_url: str
    ip_address: str | None = None
    device_fingerprint: str | None = None


class MobileDigitalSignatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID | None = None
    signer_id: UUID
    patient_id: UUID | None = None
    signature_type: str
    target_entity_type: str
    target_entity_id: UUID
    signature_image_url: str
    ip_address: str | None = None
    device_fingerprint: str | None = None
    signed_at: datetime
    created_at: datetime


class MobileClinicalMediaCreate(BaseModel):
    patient_id: UUID
    treatment_id: UUID | None = None
    media_type: MobileMediaType = MobileMediaType.INTRAORAL_PHOTO
    tooth_number: int | None = Field(default=None, ge=11, le=48)
    file_url: str
    file_size_bytes: int = Field(..., ge=0)
    compression_ratio: float | None = None
    notes: str | None = None


class MobileClinicalMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID | None = None
    patient_id: UUID
    treatment_id: UUID | None = None
    captured_by_id: UUID
    media_type: str
    tooth_number: int | None = None
    file_url: str
    file_size_bytes: int
    compression_ratio: float | None = None
    notes: str | None = None
    created_at: datetime


class MobileAIAssistRequest(BaseModel):
    task_type: str = Field(..., description="CLINICAL_SUMMARY, PATIENT_EDUCATION, APPOINTMENT_OPTIMIZER")
    context_text: str
    patient_id: UUID | None = None
    procedure_name: str | None = None


class MobileAIAssistResponse(BaseModel):
    task_type: str
    suggestion: str
    confidence_score: float = 0.95
    is_advisory_only: bool = True
    disclaimer: str = "AI generated suggestion for clinician and patient assistance only. Not a medical diagnosis."
