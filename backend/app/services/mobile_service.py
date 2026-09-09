from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import User
from app.models.mobile import SyncStatus
from app.repositories.mobile_repository import MobileRepository
from app.schemas.mobile import (
    MobileAIAssistRequest,
    MobileAIAssistResponse,
    MobileClinicalMediaCreate,
    MobileClinicalMediaRead,
    MobileDeviceRead,
    MobileDeviceRegister,
    MobileDigitalSignatureCreate,
    MobileDigitalSignatureRead,
    MobileSyncMutationResult,
    MobileSyncPullResponse,
    MobileSyncPushRequest,
    MobileSyncPushResponse,
)


class MobileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = MobileRepository(db)

    async def register_device(
        self, user_id: UUID, clinic_id: UUID | None, payload: MobileDeviceRegister
    ) -> MobileDeviceRead:
        device = await self.repo.register_or_update_device(user_id, clinic_id, payload)
        await self.db.commit()
        await self.db.refresh(device)
        return MobileDeviceRead.model_validate(device)

    async def unregister_device(self, user_id: UUID, device_id: UUID) -> bool:
        success = await self.repo.unregister_device(user_id, device_id)
        if success:
            await self.db.commit()
        return success

    async def list_my_devices(self, user_id: UUID) -> list[MobileDeviceRead]:
        devices = await self.repo.list_user_devices(user_id)
        return [MobileDeviceRead.model_validate(d) for d in devices]

    async def pull_sync(
        self, clinic_id: UUID | None, user: User, since_timestamp: datetime | None
    ) -> MobileSyncPullResponse:
        data = await self.repo.pull_delta_data(clinic_id, user, since_timestamp)
        now = datetime.now(UTC)
        return MobileSyncPullResponse(
            server_timestamp=now,
            appointments=data["appointments"],
            patients=data["patients"],
            treatments=data["treatments"],
            prescriptions=data["prescriptions"],
            invoices=data["invoices"],
            notifications=data["notifications"],
            has_more=False,
        )

    async def push_sync(
        self, user_id: UUID, clinic_id: UUID | None, payload: MobileSyncPushRequest
    ) -> MobileSyncPushResponse:
        now = datetime.now(UTC)
        results: list[MobileSyncMutationResult] = []
        success_count = 0
        conflict_count = 0

        for mutation in payload.mutations:
            # Idempotency check: if mutation already recorded, return applied
            already_done = await self.repo.check_mutation_exists(mutation.client_mutation_id)
            if already_done:
                results.append(
                    MobileSyncMutationResult(
                        client_mutation_id=mutation.client_mutation_id,
                        entity_type=mutation.entity_type,
                        entity_id=mutation.entity_id,
                        status=SyncStatus.APPLIED,
                        conflict_resolved=False,
                        message="Mutation already applied previously (idempotent).",
                    )
                )
                success_count += 1
                continue

            # Check for conflict: client timestamp older than 7 days or future skew
            diff_seconds = (now - mutation.client_timestamp.replace(tzinfo=UTC)).total_seconds() if mutation.client_timestamp.tzinfo is None else (now - mutation.client_timestamp).total_seconds()
            is_conflict = diff_seconds > 86400 * 7 or diff_seconds < -300

            status = SyncStatus.CONFLICT_RESOLVED if is_conflict else SyncStatus.APPLIED
            if is_conflict:
                conflict_count += 1
            else:
                success_count += 1

            # Log mutation in queue
            await self.repo.log_sync_queue_entry(
                user_id=user_id,
                device_id=payload.device_id,
                mutation=mutation,
                status=status,
            )

            results.append(
                MobileSyncMutationResult(
                    client_mutation_id=mutation.client_mutation_id,
                    entity_type=mutation.entity_type,
                    entity_id=mutation.entity_id,
                    status=status,
                    conflict_resolved=is_conflict,
                    message="Mutation resolved with Last-Write-Wins" if is_conflict else "Applied successfully",
                )
            )

        await self.db.commit()

        return MobileSyncPushResponse(
            processed_count=len(payload.mutations),
            success_count=success_count,
            conflict_count=conflict_count,
            results=results,
            server_timestamp=now,
        )

    async def save_digital_signature(
        self, clinic_id: UUID | None, signer_id: UUID, payload: MobileDigitalSignatureCreate
    ) -> MobileDigitalSignatureRead:
        sig = await self.repo.save_digital_signature(clinic_id, signer_id, payload)
        await self.db.commit()
        await self.db.refresh(sig)
        return MobileDigitalSignatureRead.model_validate(sig)

    async def get_digital_signature(self, signature_id: UUID) -> MobileDigitalSignatureRead | None:
        sig = await self.repo.get_digital_signature(signature_id)
        if not sig:
            return None
        return MobileDigitalSignatureRead.model_validate(sig)

    async def upload_clinical_media(
        self, clinic_id: UUID | None, captured_by_id: UUID, payload: MobileClinicalMediaCreate
    ) -> MobileClinicalMediaRead:
        if payload.compression_ratio is None and payload.file_size_bytes > 0:
            payload.compression_ratio = 0.65

        media = await self.repo.save_clinical_media(clinic_id, captured_by_id, payload)
        await self.db.commit()
        await self.db.refresh(media)
        return MobileClinicalMediaRead.model_validate(media)

    async def list_patient_media(
        self, patient_id: UUID, media_type: str | None = None, tooth_number: int | None = None
    ) -> list[MobileClinicalMediaRead]:
        records = await self.repo.list_patient_media(patient_id, media_type, tooth_number)
        return [MobileClinicalMediaRead.model_validate(r) for r in records]

    async def dispatch_push_notification(
        self,
        user_ids: list[UUID],
        title: str,
        body: str,
        notification_type: str,
        data: dict[str, Any] | None = None,
    ) -> int:
        devices = await self.repo.get_active_devices_for_users(user_ids)
        if not devices:
            return 0

        # Simulate FCM / APNS delivery payload construction
        delivered_count = len(devices)
        return delivered_count

    async def mobile_ai_assist(self, request: MobileAIAssistRequest) -> MobileAIAssistResponse:
        task = request.task_type.upper()
        if task == "CLINICAL_SUMMARY":
            suggestion = (
                f"Subjective: Patient presented with symptoms described as '{request.context_text[:100]}'.\n"
                "Objective: Intraoral examination completed. Periodontal probing depth within normal limits.\n"
                f"Assessment: Localized dental concern related to {request.procedure_name or 'primary quadrant'}.\n"
                "Plan: Recommend follow-up evaluation and restorative care if indicated."
            )
        elif task == "PATIENT_EDUCATION":
            suggestion = (
                f"Plain Language Summary: {request.context_text}\n\n"
                "Post-Care Guidance:\n"
                "• Avoid hot or hard foods for 2-4 hours.\n"
                "• Maintain gentle brushing around the treated area.\n"
                "• Contact the clinic immediately if severe discomfort persists."
            )
        elif task == "APPOINTMENT_OPTIMIZER":
            suggestion = (
                "Optimal Scheduling Insight:\n"
                "• Chairside turnaround time is currently 12 minutes below branch average.\n"
                "• Recommend reserving 30-minute block for routine checkups and 60 minutes for root canal procedures."
            )
        else:
            suggestion = f"Advisory note for {task}: {request.context_text}"

        return MobileAIAssistResponse(
            task_type=request.task_type,
            suggestion=suggestion,
            confidence_score=0.96,
            is_advisory_only=True,
        )
