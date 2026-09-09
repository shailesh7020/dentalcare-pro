from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.appointment import VisitType


class PortalLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class PortalLoginResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    user_id: UUID
    patient_id: UUID
    clinic_id: UUID
    patient_name: str
    patient_number: str


class PortalRegisterRequest(BaseModel):
    clinic_slug: str
    patient_number: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    mobile_number: str


class PortalProfileUpdate(BaseModel):
    alternate_mobile: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pin_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None


class PortalPatientProfile(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_number: str
    first_name: str
    last_name: str
    email: str | None = None
    mobile_number: str
    alternate_mobile: str | None = None
    gender: str
    date_of_birth: date
    blood_group: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pin_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None
    medical_history_notes: str | None = None
    allergies: list[str] = []


class PortalAppointmentBookRequest(BaseModel):
    dentist_id: UUID | None = None
    appointment_date: date
    start_time: time
    visit_type: VisitType = VisitType.CONSULTATION
    reason: str = Field(..., max_length=255)


class PortalAppointmentCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., max_length=255)


class PortalAppointmentRead(BaseModel):
    id: UUID
    appointment_number: str
    date: date
    start_time: time
    duration_minutes: int
    status: str
    visit_type: str
    reason: str | None = None
    notes: str | None = None
    dentist_name: str | None = None


class PortalPrescriptionItemRead(BaseModel):
    id: UUID
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None


class PortalPrescriptionRead(BaseModel):
    id: UUID
    prescription_number: str
    date: date
    dentist_name: str | None = None
    diagnosis: str | None = None
    notes: str | None = None
    items: list[PortalPrescriptionItemRead] = []


class PortalInvoiceRead(BaseModel):
    id: UUID
    invoice_number: str
    date: date
    total_amount: float
    discount_amount: float
    tax_amount: float
    final_amount: float
    paid_amount: float
    balance_due: float
    status: str


class PortalTreatmentRead(BaseModel):
    id: UUID
    treatment_plan_name: str
    status: str
    start_date: date | None = None
    completion_date: date | None = None
    dentist_name: str | None = None
    notes: str | None = None


class PortalToothRead(BaseModel):
    tooth_number: int
    condition: str
    surface_details: dict | None = None
    notes: str | None = None


class PortalDocumentRead(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    file_size_bytes: int
    file_url: str
    uploaded_at: datetime


class PortalDashboardSummary(BaseModel):
    patient_id: UUID
    patient_name: str
    patient_number: str
    clinic_name: str
    next_appointment: dict | None = None
    active_prescriptions_count: int = 0
    total_balance_due: float = 0.0
    unread_messages_count: int = 0
    pending_forms_count: int = 0
