from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.models.identity import Role, User
from app.schemas.mobile import (
    MobileAIAssistRequest,
    MobileAIAssistResponse,
    MobileClinicalMediaCreate,
    MobileClinicalMediaRead,
    MobileDeviceRead,
    MobileDeviceRegister,
    MobileDigitalSignatureCreate,
    MobileDigitalSignatureRead,
    MobileSyncPullResponse,
    MobileSyncPushRequest,
    MobileSyncPushResponse,
)
from app.services.mobile_service import MobileService

router = APIRouter(prefix="/mobile", tags=["Mobile Applications & Cross-Platform"])


@router.post("/devices/register", response_model=MobileDeviceRead, status_code=status.HTTP_201_CREATED)
async def register_mobile_device(
    payload: MobileDeviceRegister,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileDeviceRead:
    service = MobileService(db)
    return await service.register_device(actor.id, actor.clinic_id, payload)


@router.delete("/devices/{device_id}", status_code=status.HTTP_200_OK)
async def unregister_mobile_device(
    device_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    service = MobileService(db)
    success = await service.unregister_device(actor.id, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found or not owned by user.")
    return {"status": "unregistered", "message": "Device successfully unregistered."}


@router.get("/devices/me", response_model=list[MobileDeviceRead])
async def list_my_mobile_devices(
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MobileDeviceRead]:
    service = MobileService(db)
    return await service.list_my_devices(actor.id)


@router.get("/sync/pull", response_model=MobileSyncPullResponse)
async def pull_offline_sync(
    since: datetime | None = Query(default=None),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileSyncPullResponse:
    service = MobileService(db)
    return await service.pull_sync(actor.clinic_id, actor, since)


@router.post("/sync/push", response_model=MobileSyncPushResponse)
async def push_offline_sync(
    payload: MobileSyncPushRequest,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileSyncPushResponse:
    service = MobileService(db)
    return await service.push_sync(actor.id, actor.clinic_id, payload)


@router.post("/signatures", response_model=MobileDigitalSignatureRead, status_code=status.HTTP_201_CREATED)
async def record_digital_signature(
    payload: MobileDigitalSignatureCreate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileDigitalSignatureRead:
    service = MobileService(db)
    return await service.save_digital_signature(actor.clinic_id, actor.id, payload)


@router.get("/signatures/{signature_id}", response_model=MobileDigitalSignatureRead)
async def get_digital_signature(
    signature_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileDigitalSignatureRead:
    service = MobileService(db)
    sig = await service.get_digital_signature(signature_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Digital signature not found.")
    if actor.role != Role.SUPER_ADMIN and actor.clinic_id is not None and sig.clinic_id != actor.clinic_id:
        raise HTTPException(status_code=403, detail="Forbidden: cross-clinic signature access not permitted.")
    return sig


@router.post("/media/upload", response_model=MobileClinicalMediaRead, status_code=status.HTTP_201_CREATED)
async def upload_clinical_media(
    payload: MobileClinicalMediaCreate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileClinicalMediaRead:
    service = MobileService(db)
    return await service.upload_clinical_media(actor.clinic_id, actor.id, payload)


@router.get("/media/patient/{patient_id}", response_model=list[MobileClinicalMediaRead])
async def list_patient_media(
    patient_id: UUID,
    media_type: str | None = Query(default=None),
    tooth_number: int | None = Query(default=None),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MobileClinicalMediaRead]:
    service = MobileService(db)
    return await service.list_patient_media(patient_id, media_type, tooth_number)


@router.post("/ai/assist", response_model=MobileAIAssistResponse)
async def mobile_ai_assist(
    payload: MobileAIAssistRequest,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileAIAssistResponse:
    service = MobileService(db)
    return await service.mobile_ai_assist(payload)


@router.get("/dashboard")
async def get_mobile_dashboard(
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Optimized single round-trip mobile summary for doctor/owner remote view."""
    from app.services.remote_access_service import RemoteAccessService

    clinic_id = actor.clinic_id
    if not clinic_id:
        from app.models.identity import Clinic
        clinic = (await db.execute(select(Clinic).limit(1))).scalar_one_or_none()
        clinic_id = clinic.id if clinic else actor.id

    return await RemoteAccessService.get_mobile_dashboard_summary(
        clinic_id=clinic_id, user=actor, db=db
    )
