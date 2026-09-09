from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime as dt_datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.treatment import FollowUpStatus, TreatmentStatus


class ProcedureBase(BaseModel):
    procedure_name: str = Field(..., min_length=1, max_length=160)
    tooth_number: str | None = Field(None, max_length=20)
    quantity: int = Field(1, ge=1, le=100)
    cost: float = Field(0.0, ge=0.0)
    duration: int = Field(30, ge=5, le=480)
    notes: str | None = None
    status: str = "COMPLETED"


class ProcedureCreate(ProcedureBase):
    pass


class ProcedureRead(ProcedureBase):
    id: UUID
    treatment_id: UUID
    created_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class FollowUpBase(BaseModel):
    follow_up_date: dt_date
    reason: str = Field(..., min_length=1, max_length=255)
    instructions: str | None = None
    status: FollowUpStatus = FollowUpStatus.SCHEDULED


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpUpdate(BaseModel):
    follow_up_date: dt_date | None = None
    reason: str | None = None
    instructions: str | None = None
    status: FollowUpStatus | None = None


class FollowUpRead(FollowUpBase):
    id: UUID
    treatment_id: UUID
    clinic_id: UUID
    patient_id: UUID
    completed_at: dt_datetime | None = None
    created_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class SOAPNotes(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None


class TreatmentBase(BaseModel):
    patient_id: UUID
    appointment_id: UUID
    dentist_id: UUID
    diagnosis: str = Field(..., min_length=1)
    chief_complaint: str | None = None
    clinical_findings: str | None = None
    treatment_plan: str | None = None
    procedure_performed: str | None = None
    local_anaesthesia_used: str | None = None
    medicines_used: str | None = None
    clinical_notes: str | None = None
    soap: SOAPNotes | None = None
    follow_up_instructions: str | None = None
    status: TreatmentStatus = TreatmentStatus.IN_PROGRESS
    is_override: bool = False


class TreatmentCreate(TreatmentBase):
    procedures: list[ProcedureCreate] = []
    follow_up: FollowUpCreate | None = None


class TreatmentUpdate(BaseModel):
    diagnosis: str | None = None
    chief_complaint: str | None = None
    clinical_findings: str | None = None
    treatment_plan: str | None = None
    procedure_performed: str | None = None
    local_anaesthesia_used: str | None = None
    medicines_used: str | None = None
    clinical_notes: str | None = None
    soap: SOAPNotes | None = None
    follow_up_instructions: str | None = None
    status: TreatmentStatus | None = None
    procedures: list[ProcedureCreate] | None = None
    follow_up: FollowUpCreate | None = None


class TreatmentComplete(BaseModel):
    notes: str | None = None
    complete_appointment: bool = True


class TreatmentCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class TreatmentRead(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    appointment_id: UUID
    dentist_id: UUID
    treatment_number: str
    diagnosis: str
    chief_complaint: str | None = None
    clinical_findings: str | None = None
    treatment_plan: str | None = None
    procedure_performed: str | None = None
    status: TreatmentStatus
    is_override: bool = False
    created_at: dt_datetime | None = None
    completed_at: dt_datetime | None = None

    # Denormalized / Display fields
    patient_name: str | None = None
    patient_number: str | None = None
    patient_phone: str | None = None
    dentist_name: str | None = None
    appointment_number: str | None = None
    appointment_date: dt_date | None = None
    procedures_count: int = 0
    total_cost: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TreatmentDetail(TreatmentRead):
    local_anaesthesia_used: str | None = None
    medicines_used: str | None = None
    clinical_notes: str | None = None
    soap_subjective: str | None = None
    soap_objective: str | None = None
    soap_assessment: str | None = None
    soap_plan: str | None = None
    follow_up_instructions: str | None = None
    cancellation_reason: str | None = None
    procedures: list[ProcedureRead] = []
    follow_ups: list[FollowUpRead] = []
    patient_medical_alerts: list[str] = []


class TreatmentDashboardStats(BaseModel):
    planned: int
    in_progress: int
    completed: int
    follow_ups_due: int
    total_treatments: int
