from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.commercial import BackupDestination, BackupStatus, BackupType


class BackupCreateRequest(BaseModel):
    clinic_id: UUID | None = None
    backup_type: BackupType = BackupType.MANUAL
    destination_type: BackupDestination = BackupDestination.LOCAL
    is_encrypted: bool = True
    password: str | None = None
    include_media: bool = True


class BackupRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID | None = None
    file_name: str
    file_path: str
    file_size_bytes: int
    is_encrypted: bool
    checksum_sha256: str
    destination_type: str
    backup_type: str
    status: str
    created_at: datetime
    metadata_json: str | None = None


class BackupRestoreRequest(BaseModel):
    backup_id: UUID
    password: str | None = None


class BackupRestoreResponse(BaseModel):
    success: bool
    message: str
    backup_id: UUID
    restored_at: datetime
