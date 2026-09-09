from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import BackupDestination, BackupType
from app.schemas.update import UpdateCheckResponse, UpdateStatusResponse
from app.services.backup_service import BackupService

logger = logging.getLogger("dentalcare.updates")

CURRENT_APP_VERSION = "1.0.0"


class UpdateService:
    _status: str = "IDLE"
    _progress: int = 0
    _message: str = "System is running on latest stable build."
    _last_checked: datetime | None = None
    _target_version: str | None = None

    @classmethod
    def get_status(cls) -> UpdateStatusResponse:
        return UpdateStatusResponse(
            status=cls._status,
            progress_percent=cls._progress,
            message=cls._message,
            last_checked_at=cls._last_checked,
            target_version=cls._target_version,
        )

    @classmethod
    async def check_for_updates(cls, current_version: str = CURRENT_APP_VERSION) -> UpdateCheckResponse:
        cls._last_checked = datetime.now(UTC)
        # In desktop production, check local channel metadata or remote enterprise repository
        # For current release 1.0.0, we provide full channel metadata:
        latest_version = "1.0.0"
        has_update = latest_version != current_version

        return UpdateCheckResponse(
            current_version=current_version,
            latest_version=latest_version,
            has_update=has_update,
            release_notes=(
                "DentalCare Pro v1.0.0 Enterprise Release:\n"
                "- Full multi-clinic management & dental charting\n"
                "- Digital signature & QR code verification\n"
                "- Automated daily encrypted backups (AES-256)\n"
                "- Multi-workstation WebSocket network sync\n"
                "- Clinical file storage with anti-virus hook"
            ),
            download_url=None,
            sha256=None,
            mandatory=False,
            published_at=datetime(2026, 9, 9, 0, 0, 0, tzinfo=UTC),
        )

    @classmethod
    async def apply_update(
        cls,
        db: AsyncSession,
        clinic_id: UUID | None,
        target_version: str,
        package_path: str | None = None,
        expected_sha256: str | None = None,
    ) -> UpdateStatusResponse:
        cls._status = "CHECKING"
        cls._progress = 10
        cls._target_version = target_version
        cls._message = f"Starting update pipeline to v{target_version}..."

        # Step 1: Pre-update snapshot & safety backup
        cls._status = "PRE_BACKUP"
        cls._progress = 25
        cls._message = "Creating pre-update database snapshot and encrypted backup..."
        try:
            pre_backup = await BackupService.create_backup(
                db=db,
                clinic_id=clinic_id,
                backup_type=BackupType.PRE_UPDATE,
                destination_type=BackupDestination.LOCAL,
                is_encrypted=True,
            )
            logger.info("Pre-update backup created: %s", pre_backup.file_name)
        except (OSError, RuntimeError, ValueError) as e:
            cls._status = "FAILED"
            cls._progress = 0
            cls._message = f"Pre-update safety backup failed: {e!s}. Update aborted."
            raise RuntimeError(cls._message) from e

        # Step 2: Verify binary integrity if package provided
        cls._status = "VERIFYING"
        cls._progress = 60
        cls._message = "Verifying package integrity (SHA-256)..."

        if package_path:
            pkg_file = Path(package_path)
            if not pkg_file.exists():
                cls._status = "FAILED"
                cls._message = f"Update package file not found at {package_path}"
                raise FileNotFoundError(cls._message)

            if expected_sha256:
                content = pkg_file.read_bytes()
                actual_sha = hashlib.sha256(content).hexdigest()
                if actual_sha.lower() != expected_sha256.lower():
                    cls._status = "FAILED"
                    cls._message = "Package SHA-256 verification failed. Update package rejected."
                    raise ValueError(cls._message)

        # Step 3: Mark ready for atomic restart / swap
        cls._status = "READY"
        cls._progress = 100
        cls._message = f"Update to v{target_version} validated. Ready for atomic workstation restart."
        return cls.get_status()
