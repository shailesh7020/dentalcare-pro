from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime as dt_datetime
from datetime import time as dt_time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment import AppointmentStatus, ChairStatus, VisitType


class ChairBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    room_number: str | None = Field(None, max_length=40)
    status: ChairStatus = ChairStatus.ACTIVE
    notes: str | None = None


class ChairCreate(ChairBase):
    pass


class ChairUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    room_number: str | None = Field(None, max_length=40)
    status: ChairStatus | None = None
    is_active: bool | None = None
    notes: str | None = None


class ChairRead(ChairBase):
    id: UUID
    clinic_id: UUID
    is_active: bool
    created_at: dt_datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class WorkingHourCreate(BaseModel):
    dentist_id: UUID
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: dt_time
    end_time: dt_time
    break_start: dt_time | None = None
    break_end: dt_time | None = None


class WorkingHourRead(BaseModel):
    id: UUID
    clinic_id: UUID
    dentist_id: UUID
    day_of_week: int
    start_time: dt_time
    end_time: dt_time
    break_start: dt_time | None
    break_end: dt_time | None
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class BlockedTimeCreate(BaseModel):
    dentist_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=160)
    block_type: str = "LEAVE"
    start_time: dt_datetime
    end_time: dt_datetime
    is_all_day: bool = False
    notes: str | None = None


class BlockedTimeRead(BaseModel):
    id: UUID
    clinic_id: UUID
    dentist_id: UUID | None
    title: str
    block_type: str
    start_time: dt_datetime
    end_time: dt_datetime
    is_all_day: bool
    notes: str | None
    model_config = ConfigDict(from_attributes=True)


class AppointmentTimelineEventRead(BaseModel):
    id: UUID
    appointment_id: UUID
    clinic_id: UUID
    from_status: str | None
    to_status: str
    event_type: str
    title: str
    notes: str | None
    actor_id: UUID | None
    actor_name: str | None = None
    created_at: dt_datetime
    model_config = ConfigDict(from_attributes=True)


class AppointmentBase(BaseModel):
    patient_id: UUID
    dentist_id: UUID
    chair_id: UUID
    date: dt_date
    start_time: dt_time
    duration: int = Field(30, ge=5, le=480)  # minutes
    visit_type: VisitType = VisitType.CONSULTATION
    chief_complaint: str | None = None
    priority: str = "NORMAL"
    notes: str | None = None
    is_emergency_override: bool = False


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_id: UUID | None = None
    dentist_id: UUID | None = None
    chair_id: UUID | None = None
    date: dt_date | None = None
    start_time: dt_time | None = None
    duration: int | None = Field(None, ge=5, le=480)
    visit_type: VisitType | None = None
    chief_complaint: str | None = None
    priority: str | None = None
    notes: str | None = None
    is_emergency_override: bool = False


class AppointmentReschedule(BaseModel):
    new_date: dt_date
    new_start_time: dt_time
    duration: int | None = Field(None, ge=5, le=480)
    new_chair_id: UUID | None = None
    new_dentist_id: UUID | None = None
    reason: str = Field(..., min_length=1, max_length=500)
    is_emergency_override: bool = False


class AppointmentCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class AppointmentRead(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    dentist_id: UUID
    chair_id: UUID
    appointment_number: str
    date: dt_date
    start_time: dt_time
    end_time: dt_time
    duration: int
    status: AppointmentStatus
    visit_type: VisitType
    priority: str
    chief_complaint: str | None
    notes: str | None
    cancellation_reason: str | None
    is_emergency_override: bool
    created_at: dt_datetime
    updated_at: dt_datetime

    # Display / Denormalized fields
    patient_name: str | None = None
    patient_number: str | None = None
    patient_phone: str | None = None
    dentist_name: str | None = None
    chair_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentDetail(AppointmentRead):
    patient_photo_url: str | None = None
    patient_medical_alerts: list[str] = []
    timeline_events: list[AppointmentTimelineEventRead] = []


class AppointmentQueueItem(BaseModel):
    id: UUID
    appointment_number: str
    patient_id: UUID
    patient_name: str
    patient_number: str
    patient_phone: str | None
    dentist_id: UUID
    dentist_name: str
    chair_id: UUID
    chair_name: str
    scheduled_time: dt_time
    duration: int
    status: AppointmentStatus
    visit_type: VisitType
    priority: str
    checked_in_at: dt_datetime | None = None
    treatment_started_at: dt_datetime | None = None
    wait_minutes: int | None = None


class CalendarDayResponse(BaseModel):
    date: dt_date
    chairs: list[ChairRead]
    appointments: list[AppointmentRead]


class CalendarWeekResponse(BaseModel):
    start_date: dt_date
    end_date: dt_date
    appointments: list[AppointmentRead]


class CalendarMonthResponse(BaseModel):
    year: int
    month: int
    appointments: list[AppointmentRead]


class DentistScheduleRead(BaseModel):
    dentist_id: UUID
    dentist_name: str
    working_hours: list[WorkingHourRead]
    blocked_times: list[BlockedTimeRead]
    appointments: list[AppointmentRead]


class ChairScheduleRead(BaseModel):
    chair: ChairRead
    appointments: list[AppointmentRead]


class DashboardStatsResponse(BaseModel):
    date: dt_date
    total_appointments: int
    completed: int
    cancelled: int
    no_show: int
    waiting: int
    in_treatment: int
    upcoming_follow_ups: int
    revenue_placeholder: float
