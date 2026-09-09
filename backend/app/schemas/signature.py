from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.commercial import SignatureType


class ClinicianSignatureCreate(BaseModel):
    signature_data: str = Field(..., description="Base64 data URL or vector string representing signature")
    signature_type: SignatureType = Field(default=SignatureType.DRAWN, description="DRAWN or UPLOADED")


class ClinicianSignatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    signature_data: str
    signature_type: str
    verification_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SignatureVerificationResponse(BaseModel):
    is_valid: bool
    verification_hash: str
    user_id: UUID | None = None
    user_full_name: str | None = None
    role: str | None = None
    signed_at: datetime | None = None
    message: str
