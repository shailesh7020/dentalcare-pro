from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime as dt_datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.prescription import (
    DosageFrequency,
    MedicineForm,
    PrescriptionStatus,
    TemplateCategory,
)


class PrescriptionItemBase(BaseModel):
    medicine_name: str = Field(..., min_length=1, max_length=160)
    generic_name: str | None = Field(None, max_length=160)
    brand_name: str | None = Field(None, max_length=160)
    strength: str = Field(..., min_length=1, max_length=80)
    form: MedicineForm = MedicineForm.TABLET
    dosage: str = Field(..., min_length=1, max_length=80)
    route: str = Field("Oral", max_length=50)
    frequency: DosageFrequency = DosageFrequency.BD
    duration: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(10, ge=1, le=500)
    timing: str | None = Field(None, max_length=100)
    food_instructions: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)


class PrescriptionItemCreate(PrescriptionItemBase):
    pass


class PrescriptionItemUpdate(BaseModel):
    medicine_name: str | None = Field(None, min_length=1, max_length=160)
    generic_name: str | None = Field(None, max_length=160)
    brand_name: str | None = Field(None, max_length=160)
    strength: str | None = Field(None, min_length=1, max_length=80)
    form: MedicineForm | None = None
    dosage: str | None = Field(None, min_length=1, max_length=80)
    route: str | None = Field(None, max_length=50)
    frequency: DosageFrequency | None = None
    duration: str | None = Field(None, min_length=1, max_length=50)
    quantity: int | None = Field(None, ge=1, le=500)
    timing: str | None = Field(None, max_length=100)
    food_instructions: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)


class PrescriptionItemRead(PrescriptionItemBase):
    id: UUID
    prescription_id: UUID
    created_at: dt_datetime | None = None
    updated_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class MedicineCatalogBase(BaseModel):
    generic_name: str = Field(..., min_length=1, max_length=160)
    brand_name: str = Field(..., min_length=1, max_length=160)
    strength: str = Field(..., min_length=1, max_length=80)
    form: MedicineForm = MedicineForm.TABLET
    category: str = Field(..., min_length=1, max_length=100)
    standard_dosage: str | None = Field(None, max_length=120)
    default_route: str = Field("Oral", max_length=50)
    default_frequency: DosageFrequency = DosageFrequency.BD
    default_duration: str = Field("5 days", max_length=50)
    default_instructions: str | None = Field(None, max_length=255)
    notes: str | None = None


class MedicineCatalogCreate(MedicineCatalogBase):
    clinic_id: UUID | None = None


class MedicineCatalogRead(MedicineCatalogBase):
    id: UUID
    clinic_id: UUID | None = None
    is_active: bool = True
    created_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PrescriptionTemplateItem(BaseModel):
    medicine_name: str
    generic_name: str | None = None
    brand_name: str | None = None
    strength: str
    form: str = "TABLET"
    dosage: str = "1 tablet"
    route: str = "Oral"
    frequency: str = "BD"
    duration: str = "5 days"
    quantity: int = 10
    timing: str | None = None
    food_instructions: str | None = None
    notes: str | None = None


class PrescriptionTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    category: TemplateCategory = TemplateCategory.GENERAL
    description: str | None = None
    diagnosis_template: str | None = None
    instructions_template: str | None = None
    default_items: list[PrescriptionTemplateItem] = Field(default_factory=list)


class PrescriptionTemplateCreate(PrescriptionTemplateBase):
    clinic_id: UUID | None = None


class PrescriptionTemplateRead(PrescriptionTemplateBase):
    id: UUID
    clinic_id: UUID | None = None
    is_active: bool = True
    created_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PrescriptionCreate(BaseModel):
    patient_id: UUID
    treatment_id: UUID
    appointment_id: UUID
    dentist_id: UUID
    date: dt_date | None = None
    diagnosis: str = Field(..., min_length=1, max_length=1000)
    notes: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=2000)
    follow_up_date: dt_date | None = None
    items: list[PrescriptionItemCreate] = Field(default_factory=list)
    issue_immediately: bool = False


class PrescriptionUpdate(BaseModel):
    diagnosis: str | None = Field(None, min_length=1, max_length=1000)
    notes: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=2000)
    follow_up_date: dt_date | None = None
    items: list[PrescriptionItemCreate] | None = None


class PrescriptionIssue(BaseModel):
    notes: str | None = Field(None, max_length=1000)


class PrescriptionCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


class PrescriptionRead(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    treatment_id: UUID
    appointment_id: UUID
    dentist_id: UUID
    prescription_number: str
    date: dt_date
    diagnosis: str
    notes: str | None = None
    instructions: str | None = None
    follow_up_date: dt_date | None = None
    status: PrescriptionStatus
    cancellation_reason: str | None = None
    issued_at: dt_datetime | None = None
    items_count: int = 0
    created_at: dt_datetime | None = None
    updated_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PrescriptionDetail(PrescriptionRead):
    items: list[PrescriptionItemRead] = Field(default_factory=list)
    patient_name: str | None = None
    patient_number: str | None = None
    patient_age: int | None = None
    patient_gender: str | None = None
    patient_alerts: list[str] = Field(default_factory=list)
    dentist_name: str | None = None
    dentist_registration: str | None = None
    treatment_number: str | None = None
    clinic_name: str | None = None
    clinic_phone: str | None = None
    clinic_email: str | None = None


class PrescriptionDashboardStats(BaseModel):
    total_prescriptions: int = 0
    today_prescriptions: int = 0
    issued_prescriptions: int = 0
    draft_prescriptions: int = 0
    cancelled_prescriptions: int = 0
    follow_ups_due: int = 0
