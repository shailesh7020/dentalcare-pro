from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.backup import (
    BackupCreateRequest,
    BackupRecordResponse,
    BackupRestoreRequest,
    BackupRestoreResponse,
)
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backups", tags=["Backups & Disaster Recovery"])

ADMIN_ROLES = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN]


@router.post("", response_model=BackupRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    payload: BackupCreateRequest,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> BackupRecordResponse:
    clinic_id = payload.clinic_id or user.clinic_id
    try:
        record = await BackupService.create_backup(
            db=db,
            clinic_id=clinic_id,
            backup_type=payload.backup_type,
            destination_type=payload.destination_type,
            is_encrypted=payload.is_encrypted,
            password=payload.password,
        )
        return BackupRecordResponse.model_validate(record)
    except (OSError, ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {e!s}",
        )


@router.get("", response_model=list[BackupRecordResponse])
async def list_backups(
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[BackupRecordResponse]:
    clinic_id = user.clinic_id if user.role != Role.SUPER_ADMIN else None
    records = await BackupService.list_backups(db=db, clinic_id=clinic_id)
    return [BackupRecordResponse.model_validate(r) for r in records]


@router.post("/restore", response_model=BackupRestoreResponse)
async def restore_backup(
    payload: BackupRestoreRequest,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> BackupRestoreResponse:
    try:
        result = await BackupService.restore_backup(
            db=db,
            backup_id=payload.backup_id,
            password=payload.password,
        )
        return BackupRestoreResponse(
            success=result["success"],
            message=result["message"],
            backup_id=UUID(result["backup_id"]),
            restored_at=datetime.fromisoformat(result["restored_at"]),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (OSError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Restore error: {e!s}")


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: UUID,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    records = await BackupService.list_backups(db=db)
    rec = next((r for r in records if r.id == backup_id), None)
    if not rec or not Path(rec.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")

    return FileResponse(
        path=rec.file_path,
        filename=rec.file_name,
        media_type="application/octet-stream",
    )
