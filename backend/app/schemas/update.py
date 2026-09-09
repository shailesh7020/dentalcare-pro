from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UpdateCheckResponse(BaseModel):
    current_version: str
    latest_version: str
    has_update: bool
    release_notes: str
    download_url: str | None = None
    sha256: str | None = None
    mandatory: bool = False
    published_at: datetime | None = None


class UpdateApplyRequest(BaseModel):
    target_version: str
    installer_path: str | None = None


class UpdateStatusResponse(BaseModel):
    status: str = Field(..., description="IDLE, CHECKING, DOWNLOADING, READY, INSTALLING, COMPLETED, FAILED, ROLLED_BACK")
    progress_percent: int = 0
    message: str
    last_checked_at: datetime | None = None
    target_version: str | None = None
