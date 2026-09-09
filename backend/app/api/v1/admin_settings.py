from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.admin_settings import UnifiedAdminSettings
from app.services.admin_settings_service import AdminSettingsService

router = APIRouter(prefix="/settings/admin", tags=["Unified Admin Settings"])

ADMIN_ROLES = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN]


@router.get("", response_model=UnifiedAdminSettings)
async def get_admin_settings(
    clinic_id: UUID | None = Query(default=None),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> UnifiedAdminSettings:
    target_clinic_id = clinic_id or user.clinic_id
    if not target_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinic ID required to fetch administrative settings",
        )
    return await AdminSettingsService.get_unified_settings(db=db, clinic_id=target_clinic_id)


@router.put("", response_model=UnifiedAdminSettings)
async def update_admin_settings(
    payload: UnifiedAdminSettings,
    clinic_id: UUID | None = Query(default=None),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> UnifiedAdminSettings:
    target_clinic_id = clinic_id or user.clinic_id
    if not target_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clinic ID required to update administrative settings",
        )
    return await AdminSettingsService.update_unified_settings(
        db=db,
        clinic_id=target_clinic_id,
        payload=payload,
    )
