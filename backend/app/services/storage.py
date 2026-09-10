from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings


class StorageHealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check(self) -> bool:
        if self._settings.storage_backend != "local":
            return False
        path = self._settings.storage_local_path
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".healthcheck"
            probe.write_text("ok", encoding="ascii")
            probe.unlink()
            return True
        except OSError:
            return False

    async def save_patient_upload(
        self, clinic_id: UUID, patient_id: UUID, upload: UploadFile
    ) -> tuple[str, str]:
        allowed_types = {"image/jpeg", "image/png", "application/pdf"}
        if upload.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only JPEG, PNG, and PDF files are accepted",
            )
        if self._settings.storage_backend != "local":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Configured storage backend is not available",
            )
        content = await upload.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size must not exceed 10 MB",
            )
        extension = Path(upload.filename or "upload").suffix.lower()
        key = f"patients/{clinic_id}/{patient_id}/{uuid4().hex}{extension}"
        target = self._settings.storage_local_path / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return key, f"/storage/{key}"

    async def save_patient_bytes(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        content: bytes,
        filename: str,
    ) -> tuple[str, str]:
        extension = Path(filename).suffix.lower() or ".pdf"
        key = f"patients/{clinic_id}/{patient_id}/{uuid4().hex}{extension}"
        target = self._settings.storage_local_path / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return key, f"/storage/{key}"

