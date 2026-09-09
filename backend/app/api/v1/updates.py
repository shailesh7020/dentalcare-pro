from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.update import (
    UpdateApplyRequest,
    UpdateCheckResponse,
    UpdateStatusResponse,
)
from app.services.update_service import CURRENT_APP_VERSION, UpdateService

router = APIRouter(prefix="/updates", tags=["Software Updates & Maintenance"])

ADMIN_ROLES = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN]


@router.get("/check", response_model=UpdateCheckResponse)
async def check_updates(
    current_version: str = Query(default=CURRENT_APP_VERSION),
) -> UpdateCheckResponse:
    return await UpdateService.check_for_updates(current_version=current_version)


@router.get("/status", response_model=UpdateStatusResponse)
async def get_update_status() -> UpdateStatusResponse:
    return UpdateService.get_status()


@router.post("/apply", response_model=UpdateStatusResponse)
async def apply_update(
    payload: UpdateApplyRequest,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> UpdateStatusResponse:
    try:
        return await UpdateService.apply_update(
            db=db,
            clinic_id=user.clinic_id,
            target_version=payload.target_version,
            package_path=payload.installer_path,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
