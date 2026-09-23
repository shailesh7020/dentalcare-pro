from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import issue_tokens
from app.database.session import get_db
from app.models.appointment import Chair, ChairStatus
from app.models.identity import AuditEvent, Clinic, Role, User
from app.models.notification import ClinicNotificationSetting
from app.security.passwords import hash_password

router = APIRouter(prefix="/setup", tags=["First Launch Setup Wizard"])
logger = logging.getLogger("dentalcare.setup_wizard")


class SetupClinicInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    logo_data_url: str | None = None
    doctor_name: str | None = None
    registration_number: str | None = None
    gst_number: str | None = None
    email: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    website: str | None = None
    address: str | None = None
    google_maps_url: str | None = None
    notes: str | None = None


class SetupAdminAccount(BaseModel):
    username: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str | None = None
    email: str | None = None
    mobile_number: str | None = None
    profile_photo_url: str | None = None
    security_question: str | None = None
    security_answer: str | None = None


class SetupDayHours(BaseModel):
    day: str
    is_closed: bool = False
    open_time: str = "09:00"
    close_time: str = "20:00"
    morning_session: str = "09:00 - 13:30"
    evening_session: str = "16:00 - 20:00"
    lunch_break: str = "13:30 - 16:00"


class SetupChairItem(BaseModel):
    name: str
    room_number: str = "Room 101"
    color: str = "#0d9488"
    is_active: bool = True


class SetupStaffItem(BaseModel):
    name: str
    username: str
    password: str
    role: str = "RECEPTIONIST"


class SetupAppointmentSettings(BaseModel):
    default_duration_minutes: int = 30
    buffer_time_minutes: int = 5
    max_future_booking_days: int = 90
    allow_walk_ins: bool = True
    allow_double_booking: bool = False
    require_confirmation: bool = False


class SetupPatientNumberFormat(BaseModel):
    prefix: str = "PAT"
    separator: str = "-"
    include_year: bool = False
    padding_digits: int = 5
    start_number: int = 1
    auto_increment: bool = True


class SetupInvoiceSettings(BaseModel):
    receipt_prefix: str = "INV"
    receipt_number_format: str = "INV-{YYYY}-{SEQ}"
    tax_enabled: bool = False
    default_tax_percent: float = 0.0
    currency: str = "INR"
    decimal_places: int = 2
    default_payment_method: str = "CASH"


class SetupBackupSettings(BaseModel):
    auto_backup_enabled: bool = True
    frequency: str = "DAILY"
    backup_folder: str = "C:\\DentalCarePro_Backups"
    cloud_backup_enabled: bool = False
    encryption_enabled: bool = True
    password_protect: bool = False
    backup_password: str | None = None


class SetupNotificationSettings(BaseModel):
    appointment_reminder: bool = True
    birthday_reminder: bool = True
    treatment_followup: bool = True
    payment_reminder: bool = True
    channel_email: bool = True
    channel_whatsapp: bool = True
    channel_sms: bool = False


class SetupPreferences(BaseModel):
    theme: str = "light"
    language: str = "en-IN"
    date_format: str = "DD-MM-YYYY"
    time_format: str = "12h"
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"


class SetupSecuritySettings(BaseModel):
    session_timeout_minutes: int = 60
    require_password_for_delete: bool = True
    enable_audit_log: bool = True
    enable_two_factor: bool = False
    password_expiry_days: int = 0


class CompleteSetupWizardPayload(BaseModel):
    clinic: SetupClinicInfo
    admin: SetupAdminAccount
    working_hours: list[SetupDayHours] = Field(default_factory=list)
    emergency_hours: str | None = "24/7 Emergency On-Call"
    chairs: list[SetupChairItem] = Field(default_factory=list)
    staff: list[SetupStaffItem] = Field(default_factory=list)
    appointment_settings: SetupAppointmentSettings = Field(default_factory=SetupAppointmentSettings)
    patient_number_format: SetupPatientNumberFormat = Field(default_factory=SetupPatientNumberFormat)
    invoice_settings: SetupInvoiceSettings = Field(default_factory=SetupInvoiceSettings)
    backup_settings: SetupBackupSettings = Field(default_factory=SetupBackupSettings)
    notification_settings: SetupNotificationSettings = Field(default_factory=SetupNotificationSettings)
    preferences: SetupPreferences = Field(default_factory=SetupPreferences)
    security: SetupSecuritySettings = Field(default_factory=SetupSecuritySettings)


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return s[:60] or "dentalcare-clinic"


@router.get("/status")
async def get_setup_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Check whether the First Launch Clinic Setup Wizard has been completed."""
    clinic = await db.scalar(select(Clinic).order_by(Clinic.created_at.asc()))
    if not clinic:
        return {
            "is_initialized": False,
            "clinic_name": None,
            "config": {},
        }

    cfg_data: dict[str, Any] = {}
    if clinic.tax_configuration:
        try:
            parsed = json.loads(clinic.tax_configuration)
            if isinstance(parsed, dict):
                cfg_data = parsed
        except (json.JSONDecodeError, TypeError):
            pass

    is_init = bool(cfg_data.get("is_initialized", False))
    return {
        "is_initialized": is_init,
        "clinic_id": str(clinic.id),
        "clinic_name": clinic.name,
        "clinic_email": clinic.email,
        "clinic_phone": clinic.phone,
        "clinic_address": clinic.address,
        "config": cfg_data,
    }


@router.post("/complete")
async def complete_setup_wizard(
    payload: CompleteSetupWizardPayload,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Persist all 14 steps of the First Launch Setup Wizard and automatically sign in the Administrator."""
    clinic = await db.scalar(select(Clinic).order_by(Clinic.created_at.asc()))

    clinic_email = (
        payload.clinic.email
        or payload.admin.email
        or (payload.admin.username if "@" in payload.admin.username else f"{payload.admin.username}@dentalcare.com")
    ).strip().lower()

    extended_config = {
        "is_initialized": True,
        "initialized_at": datetime.now(UTC).isoformat(),
        "doctor_name": payload.clinic.doctor_name or payload.admin.full_name or "Chief Dental Surgeon",
        "registration_number": payload.clinic.registration_number,
        "tax_id_gst": payload.clinic.gst_number,
        "gst_number": payload.clinic.gst_number,
        "logo_url": payload.clinic.logo_data_url,
        "alternate_phone": payload.clinic.alternate_phone,
        "website": payload.clinic.website,
        "google_maps_url": payload.clinic.google_maps_url,
        "notes": payload.clinic.notes,
        "emergency_hours": payload.emergency_hours,
        "appointment_settings": payload.appointment_settings.model_dump(),
        "patient_number_format": payload.patient_number_format.model_dump(),
        "invoice_settings": payload.invoice_settings.model_dump(),
        "backup_settings": payload.backup_settings.model_dump(),
        "notification_settings": payload.notification_settings.model_dump(),
        "preferences": payload.preferences.model_dump(),
        "security": payload.security.model_dump(),
    }

    working_hours_json = json.dumps(
        {
            "days": [d.model_dump() for d in payload.working_hours],
            "emergency_hours": payload.emergency_hours,
            "default_appointment_duration_minutes": payload.appointment_settings.default_duration_minutes,
            "total_chairs": max(1, len(payload.chairs)),
        }
    )

    if clinic is None:
        clinic = Clinic(
            name=payload.clinic.name.strip(),
            slug=_slugify(payload.clinic.name),
            email=clinic_email,
            phone=payload.clinic.phone or payload.admin.mobile_number,
            timezone=payload.preferences.timezone or "Asia/Kolkata",
            address=payload.clinic.address,
            working_hours=working_hours_json,
            currency=payload.invoice_settings.currency or payload.preferences.currency or "INR",
            tax_configuration=json.dumps(extended_config),
            is_main_branch=True,
            is_active=True,
        )
        db.add(clinic)
        await db.flush()
    else:
        clinic.name = payload.clinic.name.strip()
        clinic.email = clinic_email
        if payload.clinic.phone or payload.admin.mobile_number:
            clinic.phone = payload.clinic.phone or payload.admin.mobile_number
        clinic.timezone = payload.preferences.timezone or "Asia/Kolkata"
        if payload.clinic.address is not None:
            clinic.address = payload.clinic.address
        clinic.working_hours = working_hours_json
        clinic.currency = payload.invoice_settings.currency or payload.preferences.currency or "INR"
        clinic.tax_configuration = json.dumps(extended_config)
        await db.flush()

    # 2. Create or update Administrator user
    raw_username = payload.admin.username.strip().lower()
    admin_email = (
        payload.admin.email.strip().lower()
        if payload.admin.email and "@" in payload.admin.email
        else (raw_username if "@" in raw_username else f"{raw_username}@dentalcare.com")
    )

    full_name = (payload.admin.full_name or payload.clinic.doctor_name or "Clinic Administrator").strip()
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "Admin"

    pw_hash = hash_password(payload.admin.password)

    admin_user = await db.scalar(select(User).where(User.email == admin_email))
    if admin_user is None:
        admin_user = User(
            clinic_id=clinic.id,
            email=admin_email,
            password_hash=pw_hash,
            first_name=first_name[:80],
            last_name=last_name[:80],
            role=Role.CLINIC_ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        await db.flush()
    else:
        admin_user.clinic_id = clinic.id
        admin_user.password_hash = pw_hash
        admin_user.first_name = first_name[:80]
        admin_user.last_name = last_name[:80]
        admin_user.role = Role.CLINIC_ADMIN
        admin_user.is_active = True
        await db.flush()

    # Also keep admin@dentalcare.com synchronized to this clinic so 1-Click Doctor Sign-In always works
    default_admin = await db.scalar(select(User).where(User.email == "admin@dentalcare.com"))
    if default_admin:
        default_admin.clinic_id = clinic.id
        default_admin.first_name = first_name[:80]
        default_admin.last_name = last_name[:80]

    # 3. Configure Treatment Rooms / Chairs (Step 5)
    existing_chairs = (await db.scalars(select(Chair).where(Chair.clinic_id == clinic.id))).all()
    existing_by_name = {c.name.lower(): c for c in existing_chairs}

    chairs_to_save = payload.chairs or [
        SetupChairItem(name="Chair 1 - Main Operatory", room_number="Room 101", color="#0d9488", is_active=True),
        SetupChairItem(name="Chair 2 - Endodontics & Hygiene", room_number="Room 102", color="#2563eb", is_active=True),
    ]
    for chair_item in chairs_to_save:
        c_name = chair_item.name.strip()
        if not c_name:
            continue
        existing_c = existing_by_name.get(c_name.lower())
        if existing_c:
            existing_c.room_number = chair_item.room_number
            existing_c.is_active = chair_item.is_active
            existing_c.status = ChairStatus.ACTIVE if chair_item.is_active else ChairStatus.MAINTENANCE
        else:
            db.add(
                Chair(
                    clinic_id=clinic.id,
                    name=c_name,
                    room_number=chair_item.room_number or "Operatory",
                    status=ChairStatus.ACTIVE if chair_item.is_active else ChairStatus.MAINTENANCE,
                    is_active=chair_item.is_active,
                )
            )

    # 4. Create Optional Staff Members (Step 6)
    role_map = {
        "RECEPTIONIST": Role.RECEPTIONIST,
        "DENTIST": Role.DENTIST,
        "ASSISTANT": Role.ASSISTANT,
        "HYGIENIST": Role.HYGIENIST,
        "MANAGER": Role.BRANCH_MANAGER,
        "CLINIC_ADMIN": Role.CLINIC_ADMIN,
    }
    for staff_member in payload.staff:
        s_user = staff_member.username.strip().lower()
        if not s_user or not staff_member.password:
            continue
        s_email = s_user if "@" in s_user else f"{s_user}@dentalcare.com"
        existing_staff = await db.scalar(select(User).where(User.email == s_email))
        s_parts = (staff_member.name.strip() or "Clinic Staff").split(" ", 1)
        s_first = s_parts[0][:80]
        s_last = (s_parts[1] if len(s_parts) > 1 else "Staff")[:80]
        s_role = role_map.get(staff_member.role.upper(), Role.RECEPTIONIST)

        if existing_staff is None:
            db.add(
                User(
                    clinic_id=clinic.id,
                    email=s_email,
                    password_hash=hash_password(staff_member.password),
                    first_name=s_first,
                    last_name=s_last,
                    role=s_role,
                    is_active=True,
                )
            )

    # 5. Configure Notification Settings (Step 11)
    notif_setting = await db.scalar(
        select(ClinicNotificationSetting).where(ClinicNotificationSetting.clinic_id == clinic.id)
    )
    if notif_setting is None:
        notif_setting = ClinicNotificationSetting(
            clinic_id=clinic.id,
            enable_email=payload.notification_settings.channel_email,
            enable_sms=payload.notification_settings.channel_sms,
            enable_whatsapp=payload.notification_settings.channel_whatsapp,
            sender_email=clinic_email,
        )
        db.add(notif_setting)
    else:
        notif_setting.enable_email = payload.notification_settings.channel_email
        notif_setting.enable_sms = payload.notification_settings.channel_sms
        notif_setting.enable_whatsapp = payload.notification_settings.channel_whatsapp

    # 6. Record Initial Audit Log Entry (Step 13/14)
    db.add(
        AuditEvent(
            id=uuid4(),
            clinic_id=clinic.id,
            actor_id=admin_user.id,
            action="INITIAL_CLINIC_SETUP",
            entity_type="CLINIC",
            entity_id=str(clinic.id),
            metadata_json=json.dumps(
                {
                    "clinic_name": clinic.name,
                    "admin_email": admin_user.email,
                    "chairs_configured": len(chairs_to_save),
                    "staff_added": len(payload.staff),
                }
            ),
        )
    )

    # 7. Issue session tokens so the Administrator is automatically logged in!
    token_pair = await issue_tokens(admin_user, db)
    await db.commit()

    return {
        "status": "completed",
        "clinic_id": str(clinic.id),
        "clinic_name": clinic.name,
        "admin_email": admin_user.email,
        "access_token": token_pair.access_token,
        "refresh_token": token_pair.refresh_token,
    }
