from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Clinic
from app.models.notification import ClinicNotificationSetting
from app.schemas.admin_settings import (
    BackupScheduleSettings,
    ClinicProfileSettings,
    GatewayCredentialsSettings,
    LocalizationSettings,
    ReminderScheduleSettings,
    UnifiedAdminSettings,
    WorkingHoursSettings,
)

logger = logging.getLogger("dentalcare.admin_settings")


class AdminSettingsService:
    @classmethod
    async def get_unified_settings(cls, db: AsyncSession, clinic_id: UUID) -> UnifiedAdminSettings:
        clinic = await db.get(Clinic, clinic_id)
        if not clinic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

        # Notification settings
        stmt = select(ClinicNotificationSetting).where(ClinicNotificationSetting.clinic_id == clinic_id)
        res = await db.execute(stmt)
        notif_setting = res.scalar_one_or_none()

        # Parse tax config if JSON
        tax_id = None
        logo_url = None
        if clinic.tax_configuration:
            try:
                t_data = json.loads(clinic.tax_configuration)
                tax_id = t_data.get("tax_id_gst")
                logo_url = t_data.get("logo_url")
            except (json.JSONDecodeError, TypeError):
                tax_id = clinic.tax_configuration

        profile = ClinicProfileSettings(
            name=clinic.name,
            legal_name=clinic.name,
            email=clinic.email,
            phone=clinic.phone,
            address=clinic.address,
            currency=clinic.currency or "INR",
            tax_id_gst=tax_id,
            logo_url=logo_url,
        )

        # Parse working hours if JSON
        wh = WorkingHoursSettings()
        if clinic.working_hours:
            try:
                wh_data = json.loads(clinic.working_hours)
                wh = WorkingHoursSettings(**wh_data)
            except Exception:
                pass

        # Notifications & Reminders
        if notif_setting:
            raw_intervals = notif_setting.reminder_intervals_hours
            if isinstance(raw_intervals, (list, tuple)):
                intervals_str = ",".join(str(x) for x in raw_intervals)
            else:
                intervals_str = str(raw_intervals or "168,72,24,2")

            reminders = ReminderScheduleSettings(
                reminder_intervals_hours=intervals_str,
                enable_sms=notif_setting.enable_sms,
                enable_email=notif_setting.enable_email,
                enable_whatsapp=notif_setting.enable_whatsapp,
                enable_missed_visit_followups=True,
            )
            gateways = GatewayCredentialsSettings(
                smtp_from_email=notif_setting.sender_email,
                sms_gateway_provider="Default SMS Gateway" if notif_setting.enable_sms else None,
            )
        else:
            reminders = ReminderScheduleSettings()
            gateways = GatewayCredentialsSettings()

        # Backup & Localization
        backup_sched = BackupScheduleSettings()
        localization = LocalizationSettings(
            timezone=clinic.timezone or "Asia/Kolkata",
            date_format="DD-MM-YYYY",
            language="en",
        )

        return UnifiedAdminSettings(
            clinic_profile=profile,
            working_hours=wh,
            backup_schedule=backup_sched,
            reminder_schedule=reminders,
            gateways=gateways,
            localization=localization,
        )

    @classmethod
    async def update_unified_settings(
        cls,
        db: AsyncSession,
        clinic_id: UUID,
        payload: UnifiedAdminSettings,
    ) -> UnifiedAdminSettings:
        clinic = await db.get(Clinic, clinic_id)
        if not clinic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

        # 1. Update Clinic profile
        clinic.name = payload.clinic_profile.name
        clinic.email = payload.clinic_profile.email
        clinic.phone = payload.clinic_profile.phone
        clinic.address = payload.clinic_profile.address
        clinic.currency = payload.clinic_profile.currency
        clinic.timezone = payload.localization.timezone

        tax_config_payload = {
            "tax_id_gst": payload.clinic_profile.tax_id_gst,
            "legal_name": payload.clinic_profile.legal_name,
            "logo_url": payload.clinic_profile.logo_url,
        }
        clinic.tax_configuration = json.dumps(tax_config_payload)
        clinic.working_hours = json.dumps(payload.working_hours.model_dump())

        # 2. Update Notification Settings
        stmt = select(ClinicNotificationSetting).where(ClinicNotificationSetting.clinic_id == clinic_id)
        res = await db.execute(stmt)
        notif_setting = res.scalar_one_or_none()

        if not notif_setting:
            notif_setting = ClinicNotificationSetting(
                clinic_id=clinic_id,
                enable_email=payload.reminder_schedule.enable_email,
                enable_sms=payload.reminder_schedule.enable_sms,
                enable_whatsapp=payload.reminder_schedule.enable_whatsapp,
                reminder_intervals_hours=payload.reminder_schedule.reminder_intervals_hours,
                sender_email=payload.gateways.smtp_from_email or clinic.email,
                sender_phone=clinic.phone,
            )
            db.add(notif_setting)
        else:
            notif_setting.enable_email = payload.reminder_schedule.enable_email
            notif_setting.enable_sms = payload.reminder_schedule.enable_sms
            notif_setting.enable_whatsapp = payload.reminder_schedule.enable_whatsapp
            notif_setting.reminder_intervals_hours = payload.reminder_schedule.reminder_intervals_hours
            if payload.gateways.smtp_from_email:
                notif_setting.sender_email = payload.gateways.smtp_from_email

        await db.commit()
        await db.refresh(clinic)
        return await cls.get_unified_settings(db, clinic_id)
