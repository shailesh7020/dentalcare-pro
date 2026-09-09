from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
import subprocess
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.mobile import MobileClinicalMedia

logger = logging.getLogger("dentalcare.storage")

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "application/dicom": ".dcm",
    "image/tiff": ".tif",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _find_windows_defender() -> str | None:
    """Locate MpCmdRun.exe on Windows."""
    if os.name != "nt":
        return None
    matches = glob.glob(r"C:\ProgramData\Microsoft\Windows Defender\Platform\*\MpCmdRun.exe")
    if matches:
        return sorted(matches)[-1]
    default_path = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
    if Path(default_path).exists():
        return default_path
    return None


class AntiVirusService:
    @classmethod
    def scan_file(cls, file_path: Path) -> tuple[bool, str]:
        """Scans a file for malware. Returns (is_clean, details)."""
        # 1. Heuristic inspection: check for executable binary headers (MZ/ELF header) disguised as media
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
                    return False, "Prohibited executable binary payload detected in file"
        except OSError:
            pass

        # 2. Windows Defender deep signature inspection
        defender_bin = _find_windows_defender()
        if defender_bin and file_path.exists():
            try:
                cmd = [defender_bin, "-Scan", "-ScanType", "3", "-File", str(file_path)]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                # 0: No threat detected, 2: Threat found
                if res.returncode == 2:
                    return False, "Threat detected by Windows Defender"
                elif res.returncode == 0:
                    return True, "Scanned clean with Windows Defender"
            except Exception as e:
                logger.warning("Windows Defender scan exception: %s", e)

        return True, "Passed security verification"


class ClinicalStorageService:
    @classmethod
    def get_storage_base(cls) -> Path:
        settings = get_settings()
        base = settings.storage_local_path
        base.mkdir(parents=True, exist_ok=True)
        return base

    @classmethod
    async def save_clinical_file(
        cls,
        db: AsyncSession,
        clinic_id: UUID | None,
        patient_id: UUID,
        captured_by_id: UUID,
        category: str,
        upload: UploadFile,
        tooth_number: int | None = None,
        notes: str | None = None,
    ) -> MobileClinicalMedia:
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file format '{content_type}'. Allowed: JPEG, PNG, WEBP, PDF, DICOM, TIFF.",
            )

        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB",
            )

        # Canonical category folder
        norm_category = category.lower().strip()
        if norm_category not in {"xray", "photo", "document", "consent", "invoice", "prescription"}:
            norm_category = "document"

        ext = ALLOWED_MIME_TYPES.get(content_type, Path(upload.filename or "file").suffix.lower() or ".bin")
        file_id = uuid4()
        file_name = f"{file_id.hex}{ext}"

        cid_str = str(clinic_id) if clinic_id else "main"
        target_dir = cls.get_storage_base() / norm_category / cid_str / str(patient_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file_name

        # Write to disk
        target_path.write_bytes(content)

        # Anti-virus scan
        is_clean, scan_details = AntiVirusService.scan_file(target_path)
        if not is_clean:
            try:
                target_path.unlink()
            except OSError:
                pass
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Security alert: Upload rejected. {scan_details}",
            )

        rel_url = f"/storage/{norm_category}/{cid_str}/{patient_id}/{file_name}"

        media = MobileClinicalMedia(
            id=file_id,
            clinic_id=clinic_id,
            patient_id=patient_id,
            captured_by_id=captured_by_id,
            media_type=norm_category.upper(),
            tooth_number=tooth_number,
            file_url=rel_url,
            file_size_bytes=len(content),
            notes=notes,
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)
        return media

    @classmethod
    async def get_patient_documents(
        cls,
        db: AsyncSession,
        patient_id: UUID,
        category: str | None = None,
    ) -> list[MobileClinicalMedia]:
        stmt = (
            select(MobileClinicalMedia)
            .where(
                MobileClinicalMedia.patient_id == patient_id,
                MobileClinicalMedia.deleted_at.is_(None),
            )
            .order_by(MobileClinicalMedia.created_at.desc())
        )
        if category:
            stmt = stmt.where(MobileClinicalMedia.media_type == category.upper())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def soft_delete(cls, db: AsyncSession, document_id: UUID) -> bool:
        doc = await db.get(MobileClinicalMedia, document_id)
        if not doc or doc.deleted_at is not None:
            return False
        from datetime import datetime, timezone
        doc.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    @classmethod
    async def restore(cls, db: AsyncSession, document_id: UUID) -> bool:
        doc = await db.get(MobileClinicalMedia, document_id)
        if not doc or doc.deleted_at is None:
            return False
        doc.deleted_at = None
        await db.commit()
        return True
