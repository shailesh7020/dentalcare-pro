from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ClinicProfileSettings(BaseModel):
    name: str = Field(..., max_length=160)
    legal_name: str | None = None
    email: str = Field(..., max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    currency: str = Field(default="INR", max_length=10)
    tax_id_gst: str | None = Field(default=None, max_length=64)
    logo_url: str | None = None


class WorkingHoursSettings(BaseModel):
    monday_friday: str = "09:00 - 18:00"
    saturday: str = "09:00 - 14:00"
    sunday: str = "Closed"
    default_appointment_duration_minutes: int = Field(default=30, ge=5, le=180)
    total_chairs: int = Field(default=3, ge=1, le=50)


class BackupScheduleSettings(BaseModel):
    daily_backup_enabled: bool = True
    backup_time_utc: str = Field(default="23:00", description="HH:MM in 24-hour UTC format")
    retention_days: int = Field(default=30, ge=1, le=365)
    encrypt_backups: bool = True
    destination_type: str = Field(default="LOCAL", description="LOCAL, EXTERNAL, NETWORK, S3")


class ReminderScheduleSettings(BaseModel):
    reminder_intervals_hours: str = Field(default="168,72,24,2", description="Comma-separated hours before visit")
    enable_sms: bool = False
    enable_email: bool = True
    enable_whatsapp: bool = False
    enable_missed_visit_followups: bool = True


class GatewayCredentialsSettings(BaseModel):
    sms_gateway_provider: str | None = None
    sms_api_key: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_api_token: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None


class LocalizationSettings(BaseModel):
    timezone: str = "Asia/Kolkata"
    date_format: str = "DD-MM-YYYY"
    language: str = "en"


class UnifiedAdminSettings(BaseModel):
    clinic_profile: ClinicProfileSettings
    working_hours: WorkingHoursSettings
    backup_schedule: BackupScheduleSettings
    reminder_schedule: ReminderScheduleSettings
    gateways: GatewayCredentialsSettings
    localization: LocalizationSettings
