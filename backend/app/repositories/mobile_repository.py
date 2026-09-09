from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.billing import Invoice
from app.models.identity import Role, User
from app.models.mobile import (
    MobileClinicalMedia,
    MobileDevice,
    MobileDigitalSignature,
    MobileSyncQueue,
    SyncStatus,
    SyncType,
)
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.treatment import Treatment
from app.schemas.mobile import (
    MobileClinicalMediaCreate,
    MobileDeviceRegister,
    MobileDigitalSignatureCreate,
    MobileMutation,
)


class MobileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_or_update_device(
        self, user_id: UUID, clinic_id: UUID | None, payload: MobileDeviceRegister
    ) -> MobileDevice:
        now = datetime.now(UTC)
        query = select(MobileDevice).where(
            MobileDevice.user_id == user_id,
            MobileDevice.device_token == payload.device_token,
            MobileDevice.deleted_at.is_(None),
        )
        res = await self.db.execute(query)
        device = res.scalar_one_or_none()

        if device:
            device.clinic_id = clinic_id
            device.device_type = payload.device_type.value if hasattr(payload.device_type, "value") else str(payload.device_type)
            device.device_name = payload.device_name
            device.device_os_version = payload.device_os_version
            device.app_version = payload.app_version
            device.biometric_enabled = payload.biometric_enabled
            device.is_active = True
            device.last_active_at = now
            device.updated_at = now
        else:
            device = MobileDevice(
                user_id=user_id,
                clinic_id=clinic_id,
                device_token=payload.device_token,
                device_type=payload.device_type.value if hasattr(payload.device_type, "value") else str(payload.device_type),
                device_name=payload.device_name,
                device_os_version=payload.device_os_version,
                app_version=payload.app_version,
                is_active=True,
                last_active_at=now,
                biometric_enabled=payload.biometric_enabled,
            )
            self.db.add(device)

        await self.db.flush()
        return device

    async def unregister_device(self, user_id: UUID, device_id: UUID) -> bool:
        query = select(MobileDevice).where(
            MobileDevice.id == device_id,
            MobileDevice.user_id == user_id,
            MobileDevice.deleted_at.is_(None),
        )
        res = await self.db.execute(query)
        device = res.scalar_one_or_none()
        if not device:
            return False

        device.is_active = False
        device.updated_at = datetime.now(UTC)
        await self.db.flush()
        return True

    async def list_user_devices(self, user_id: UUID) -> list[MobileDevice]:
        query = select(MobileDevice).where(
            MobileDevice.user_id == user_id,
            MobileDevice.deleted_at.is_(None),
            MobileDevice.is_active.is_(True),
        ).order_by(desc(MobileDevice.last_active_at))
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_active_devices_for_users(self, user_ids: list[UUID]) -> list[MobileDevice]:
        if not user_ids:
            return []
        query = select(MobileDevice).where(
            MobileDevice.user_id.in_(user_ids),
            MobileDevice.is_active.is_(True),
            MobileDevice.deleted_at.is_(None),
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def check_mutation_exists(self, client_mutation_id: str) -> bool:
        query = select(MobileSyncQueue.id).where(
            MobileSyncQueue.client_mutation_id == client_mutation_id,
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none() is not None

    async def log_sync_queue_entry(
        self,
        user_id: UUID,
        device_id: UUID | None,
        mutation: MobileMutation,
        status: SyncStatus,
    ) -> MobileSyncQueue:
        now = datetime.now(UTC)
        entry = MobileSyncQueue(
            user_id=user_id,
            device_id=device_id,
            sync_type=SyncType.PUSH.value,
            entity_type=mutation.entity_type,
            entity_id=mutation.entity_id,
            client_mutation_id=mutation.client_mutation_id,
            status=status.value if hasattr(status, "value") else str(status),
            client_timestamp=mutation.client_timestamp,
            server_timestamp=now,
            payload_json=json.dumps(mutation.payload) if mutation.payload else None,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def save_digital_signature(
        self, clinic_id: UUID | None, signer_id: UUID, payload: MobileDigitalSignatureCreate
    ) -> MobileDigitalSignature:
        now = datetime.now(UTC)
        sig = MobileDigitalSignature(
            clinic_id=clinic_id,
            signer_id=signer_id,
            patient_id=payload.patient_id,
            signature_type=payload.signature_type.value if hasattr(payload.signature_type, "value") else str(payload.signature_type),
            target_entity_type=payload.target_entity_type,
            target_entity_id=payload.target_entity_id,
            signature_image_url=payload.signature_image_url,
            ip_address=payload.ip_address,
            device_fingerprint=payload.device_fingerprint,
            signed_at=now,
        )
        self.db.add(sig)
        await self.db.flush()
        return sig

    async def get_digital_signature(self, signature_id: UUID) -> MobileDigitalSignature | None:
        query = select(MobileDigitalSignature).where(
            MobileDigitalSignature.id == signature_id,
            MobileDigitalSignature.deleted_at.is_(None),
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def save_clinical_media(
        self, clinic_id: UUID | None, captured_by_id: UUID, payload: MobileClinicalMediaCreate
    ) -> MobileClinicalMedia:
        media = MobileClinicalMedia(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            treatment_id=payload.treatment_id,
            captured_by_id=captured_by_id,
            media_type=payload.media_type.value if hasattr(payload.media_type, "value") else str(payload.media_type),
            tooth_number=payload.tooth_number,
            file_url=payload.file_url,
            file_size_bytes=payload.file_size_bytes,
            compression_ratio=payload.compression_ratio,
            notes=payload.notes,
        )
        self.db.add(media)
        await self.db.flush()
        return media

    async def list_patient_media(
        self, patient_id: UUID, media_type: str | None = None, tooth_number: int | None = None
    ) -> list[MobileClinicalMedia]:
        query = select(MobileClinicalMedia).where(
            MobileClinicalMedia.patient_id == patient_id,
            MobileClinicalMedia.deleted_at.is_(None),
        )
        if media_type:
            query = query.where(MobileClinicalMedia.media_type == media_type)
        if tooth_number is not None:
            query = query.where(MobileClinicalMedia.tooth_number == tooth_number)

        query = query.order_by(desc(MobileClinicalMedia.created_at))
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def pull_delta_data(
        self,
        clinic_id: UUID | None,
        user: User,
        since_timestamp: datetime | None,
    ) -> dict[str, list[dict[str, Any]]]:
        results: dict[str, list[dict[str, Any]]] = {
            "appointments": [],
            "patients": [],
            "treatments": [],
            "prescriptions": [],
            "invoices": [],
            "notifications": [],
        }

        # Appointments
        appt_query = select(Appointment).where(Appointment.deleted_at.is_(None))
        if clinic_id:
            appt_query = appt_query.where(Appointment.clinic_id == clinic_id)
        if user.role == Role.PATIENT and getattr(user, "patient_id", None):
            appt_query = appt_query.where(Appointment.patient_id == user.patient_id)
        elif user.role == Role.DENTIST and getattr(user, "dentist_id", None):
            appt_query = appt_query.where(Appointment.dentist_id == user.dentist_id)
        if since_timestamp:
            appt_query = appt_query.where(Appointment.updated_at > since_timestamp)
        appt_query = appt_query.order_by(desc(Appointment.date)).limit(100)
        appts = (await self.db.execute(appt_query)).scalars().all()
        results["appointments"] = [
            {
                "id": str(a.id),
                "clinic_id": str(a.clinic_id),
                "patient_id": str(a.patient_id),
                "dentist_id": str(a.dentist_id),
                "date": a.date.isoformat() if a.date else None,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "status": a.status,
                "reason": a.reason,
            }
            for a in appts
        ]

        # Patients
        pat_query = select(Patient).where(Patient.deleted_at.is_(None))
        if clinic_id:
            pat_query = pat_query.where(Patient.clinic_id == clinic_id)
        if user.role == Role.PATIENT and user.patient_id:
            pat_query = pat_query.where(Patient.id == user.patient_id)
        if since_timestamp:
            pat_query = pat_query.where(Patient.updated_at > since_timestamp)
        pat_query = pat_query.limit(50)
        patients = (await self.db.execute(pat_query)).scalars().all()
        results["patients"] = [
            {
                "id": str(p.id),
                "clinic_id": str(p.clinic_id),
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone": p.phone,
                "email": p.email,
                "blood_group": p.blood_group,
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            }
            for p in patients
        ]

        # Treatments
        treat_query = select(Treatment).where(Treatment.deleted_at.is_(None))
        if clinic_id:
            treat_query = treat_query.where(Treatment.clinic_id == clinic_id)
        if user.role == Role.PATIENT and user.patient_id:
            treat_query = treat_query.where(Treatment.patient_id == user.patient_id)
        if since_timestamp:
            treat_query = treat_query.where(Treatment.updated_at > since_timestamp)
        treat_query = treat_query.limit(50)
        treatments = (await self.db.execute(treat_query)).scalars().all()
        results["treatments"] = [
            {
                "id": str(t.id),
                "clinic_id": str(t.clinic_id),
                "patient_id": str(t.patient_id),
                "dentist_id": str(t.dentist_id),
                "status": t.status,
                "diagnosis": t.diagnosis,
                "total_cost": float(t.total_cost or 0),
            }
            for t in treatments
        ]

        # Prescriptions
        rx_query = select(Prescription).where(Prescription.deleted_at.is_(None))
        if clinic_id:
            rx_query = rx_query.where(Prescription.clinic_id == clinic_id)
        if user.role == Role.PATIENT and user.patient_id:
            rx_query = rx_query.where(Prescription.patient_id == user.patient_id)
        if since_timestamp:
            rx_query = rx_query.where(Prescription.updated_at > since_timestamp)
        rx_query = rx_query.limit(50)
        rxs = (await self.db.execute(rx_query)).scalars().all()
        results["prescriptions"] = [
            {
                "id": str(rx.id),
                "clinic_id": str(rx.clinic_id),
                "patient_id": str(rx.patient_id),
                "dentist_id": str(rx.dentist_id),
                "status": rx.status,
                "notes": rx.notes,
            }
            for rx in rxs
        ]

        # Invoices
        inv_query = select(Invoice).where(Invoice.deleted_at.is_(None))
        if clinic_id:
            inv_query = inv_query.where(Invoice.clinic_id == clinic_id)
        if user.role == Role.PATIENT and user.patient_id:
            inv_query = inv_query.where(Invoice.patient_id == user.patient_id)
        if since_timestamp:
            inv_query = inv_query.where(Invoice.updated_at > since_timestamp)
        inv_query = inv_query.limit(50)
        invs = (await self.db.execute(inv_query)).scalars().all()
        results["invoices"] = [
            {
                "id": str(inv.id),
                "clinic_id": str(inv.clinic_id),
                "patient_id": str(inv.patient_id),
                "status": inv.status,
                "invoice_number": inv.invoice_number,
                "total_amount": float(inv.total_amount or 0),
                "balance_due": float(inv.balance_due or 0),
            }
            for inv in invs
        ]

        # Notifications
        notif_query = select(Notification).where(Notification.deleted_at.is_(None))
        if clinic_id:
            notif_query = notif_query.where(Notification.clinic_id == clinic_id)
        if user.role == Role.PATIENT:
            notif_query = notif_query.where(Notification.patient_id == user.patient_id)
        if since_timestamp:
            notif_query = notif_query.where(Notification.updated_at > since_timestamp)
        notif_query = notif_query.limit(50)
        notifs = (await self.db.execute(notif_query)).scalars().all()
        results["notifications"] = [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "status": n.status,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifs
        ]

        return results
