from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.odontogram import NumberingSystem, ToothSurfaceEnum


class ToothSurfaceRead(BaseModel):
    id: UUID
    surface: str
    condition: str
    treatment: str
    color: str
    notes: str | None = None
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dentist_id: UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class ToothSurfaceUpdate(BaseModel):
    condition: str | None = None
    treatment: str | None = None
    color: str | None = None
    notes: str | None = None


class ToothHistoryRead(BaseModel):
    id: UUID
    tooth_id: UUID
    action: str
    description: str
    previous_state: str | None = None
    new_state: str | None = None
    affected_surfaces: str | None = None
    treatment_id: UUID | None = None
    treatment_procedure_id: UUID | None = None
    appointment_id: UUID | None = None
    dentist_id: UUID | None = None
    created_at: datetime
    created_by: UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class ToothRead(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    tooth_number: str
    universal_number: str
    palmer_notation: str
    name: str
    dentition_type: str
    arch: str
    quadrant: int
    tooth_type: str
    primary_status: str
    color: str
    is_missing: bool
    is_extracted: bool
    is_impacted: bool
    has_root_canal: bool
    has_crown: bool
    has_implant: bool
    has_bridge: bool
    mobility_grade: int
    notes: str | None = None
    surfaces: list[ToothSurfaceRead] = []
    model_config = ConfigDict(from_attributes=True)


class ToothDetail(ToothRead):
    history: list[ToothHistoryRead] = []


class ToothUpdate(BaseModel):
    primary_status: str | None = None
    color: str | None = None
    is_missing: bool | None = None
    is_extracted: bool | None = None
    is_impacted: bool | None = None
    has_root_canal: bool | None = None
    has_crown: bool | None = None
    has_implant: bool | None = None
    has_bridge: bool | None = None
    mobility_grade: int | None = None
    notes: str | None = None


class ToothConditionCreate(BaseModel):
    condition: str = Field(..., min_length=1, max_length=60)
    surfaces: list[ToothSurfaceEnum] | None = None
    notes: str | None = None
    color: str | None = None


class ToothProcedureCreate(BaseModel):
    procedure_name: str = Field(..., min_length=1, max_length=160)
    procedure_type: str = Field(..., min_length=1, max_length=60)
    surfaces: list[ToothSurfaceEnum] | None = None
    material: str | None = None
    cost: float = Field(0.0, ge=0.0)
    notes: str | None = None
    treatment_id: UUID | None = None
    appointment_id: UUID | None = None


class OdontogramDashboardStats(BaseModel):
    active_caries: int = 0
    missing_teeth: int = 0
    root_canals: int = 0
    crowns: int = 0
    implants: int = 0
    restorations: int = 0
    total_teeth_charted: int = 0


class PatientOdontogramRead(BaseModel):
    patient_id: UUID
    patient_name: str
    patient_number: str
    dentition_type: str = "ADULT"
    preferred_numbering: NumberingSystem = NumberingSystem.FDI
    teeth: list[ToothRead]
    stats: OdontogramDashboardStats
