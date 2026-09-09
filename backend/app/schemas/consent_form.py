from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.consent_form import FormStatus, FormType


class FormTemplateBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str = Field(..., max_length=200)
    description: str | None = None
    form_type: FormType = FormType.CUSTOM
    schema_json: str
    is_active: bool = True


class FormTemplateCreate(FormTemplateBase):
    pass


class FormTemplateUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str | None = None
    description: str | None = None
    form_type: FormType | None = None
    schema_json: str | None = None
    is_active: bool | None = None


class FormTemplateRead(FormTemplateBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    clinic_id: UUID | None = None
    version: int
    created_at: datetime


class PatientFormCreate(BaseModel):
    patient_id: UUID
    template_id: UUID
    answers_json: str = "{}"


class PatientFormSubmit(BaseModel):
    answers_json: str


class PatientFormReview(BaseModel):
    status: FormStatus
    notes: str | None = None


class PatientFormRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    patient_name: str | None = None
    template_id: UUID
    template_title: str | None = None
    status: FormStatus
    answers_json: str
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by_id: UUID | None = None
    reviewed_by_name: str | None = None
    notes: str | None = None
    created_at: datetime


class ConsentRecordCreate(BaseModel):
    patient_id: UUID
    treatment_id: UUID | None = None
    consent_type: str = Field(..., max_length=80)
    title: str = Field(..., max_length=200)
    content_text: str
    patient_signature: str
    witness_name: str | None = None
    expires_at: date | None = None


class ConsentSignaturePayload(BaseModel):
    patient_signature: str
    witness_name: str | None = None


class ConsentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    patient_name: str | None = None
    treatment_id: UUID | None = None
    consent_type: str
    title: str
    content_text: str
    patient_signature: str
    signed_at: datetime | None = None
    ip_address: str | None = None
    witness_name: str | None = None
    version: int
    expires_at: date | None = None
    created_at: datetime
