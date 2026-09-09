from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.identity import Clinic
from app.models.notification import ClinicNotificationSetting
from app.services.admin_settings_service import AdminSettingsService


class MockAdminDb:
    def __init__(self, clinic: Clinic | None = None, notif: ClinicNotificationSetting | None = None) -> None:
        self.clinic = clinic
        self.notif = notif
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)
        if isinstance(obj, ClinicNotificationSetting):
            self.notif = obj

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        pass

    async def get(self, entity_cls: type, ident: object) -> object | None:
        if entity_cls is Clinic and self.clinic and self.clinic.id == ident:
            return self.clinic
        return None

    async def execute(self, stmt: object) -> MagicMock:
        res = MagicMock()
        res.scalar_one_or_none.return_value = self.notif
        return res


@pytest.mark.asyncio
async def test_get_unified_settings_success():
    """Verify loading unified admin settings with JSON tax and working hours."""
    clinic_id = uuid4()
    tax_payload = json.dumps({"tax_id_gst": "27AABCU9603R1ZM", "logo_url": "https://example.com/logo.png"})
    wh_payload = json.dumps({"monday_friday": "09:00 - 18:00", "saturday": "09:00 - 14:00"})

    clinic = Clinic(
        id=clinic_id,
        name="Apex Dental Care",
        email="apex@example.com",
        phone="+919876543210",
        address="123 Park Street, Mumbai",
        currency="INR",
        timezone="Asia/Kolkata",
        tax_configuration=tax_payload,
        working_hours=wh_payload,
    )
    notif = ClinicNotificationSetting(
        clinic_id=clinic_id,
        enable_email=True,
        enable_sms=True,
        enable_whatsapp=False,
        reminder_intervals_hours="24,2",
        sender_email="no-reply@apexdental.com",
    )

    db = MockAdminDb(clinic=clinic, notif=notif)

    settings = await AdminSettingsService.get_unified_settings(db, clinic_id)  # type: ignore

    assert settings.clinic_profile.name == "Apex Dental Care"
    assert settings.clinic_profile.tax_id_gst == "27AABCU9603R1ZM"
    assert settings.working_hours.monday_friday == "09:00 - 18:00"
    assert settings.reminder_schedule.enable_email is True
    assert settings.reminder_schedule.reminder_intervals_hours == "24,2"
    assert settings.gateways.smtp_from_email == "no-reply@apexdental.com"


@pytest.mark.asyncio
async def test_get_unified_settings_not_found():
    """Verify 404 is thrown when clinic ID does not exist."""
    db = MockAdminDb(clinic=None)
    with pytest.raises(HTTPException) as exc_info:
        await AdminSettingsService.get_unified_settings(db, uuid4())  # type: ignore

    assert exc_info.value.status_code == 404
    assert "Clinic not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_unified_settings():
    """Verify updating clinic profile, tax information, and notification settings."""
    clinic_id = uuid4()
    clinic = Clinic(
        id=clinic_id,
        name="Old Clinic Name",
        email="old@example.com",
        phone="+919000000000",
        currency="INR",
    )
    db = MockAdminDb(clinic=clinic, notif=None)

    current = await AdminSettingsService.get_unified_settings(db, clinic_id)  # type: ignore
    current.clinic_profile.name = "Modern Dental Specialists"
    current.clinic_profile.tax_id_gst = "29ABCDE1234F1Z5"
    current.working_hours.saturday = "09:00 - 13:00"
    current.reminder_schedule.enable_whatsapp = True

    updated = await AdminSettingsService.update_unified_settings(db, clinic_id, current)  # type: ignore

    assert updated.clinic_profile.name == "Modern Dental Specialists"
    assert updated.clinic_profile.tax_id_gst == "29ABCDE1234F1Z5"
    assert updated.working_hours.saturday == "09:00 - 13:00"
    assert updated.reminder_schedule.enable_whatsapp is True
