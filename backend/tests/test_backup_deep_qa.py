from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
from uuid import uuid4
import zipfile

from cryptography.fernet import Fernet
import pytest

from app.models.commercial import BackupDestination, BackupRecord, BackupStatus, BackupType
from app.services.backup_service import BackupService, _derive_fernet_key, get_default_backup_dir


class MockAsyncDb:
    def __init__(self, records: list[BackupRecord] | None = None) -> None:
        self.records: dict[str, BackupRecord] = {}
        for r in (records or []):
            if getattr(r, "id", None) is None:
                r.id = uuid4()
            self.records[str(r.id)] = r
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        self.added.append(obj)
        if isinstance(obj, BackupRecord):
            self.records[str(obj.id)] = obj

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: object) -> None:
        pass

    async def get(self, entity_cls: type, ident: object) -> object | None:
        if entity_cls is BackupRecord:
            return self.records.get(str(ident))
        return None

    async def execute(self, stmt: object) -> MagicMock:
        res = MagicMock()
        # Empty list so prune_old_backups does not prune active test records
        res.scalars.return_value.all.return_value = []
        return res


@pytest.mark.asyncio
async def test_derive_fernet_key():
    """Verify deterministic derivation of 32-byte Fernet key."""
    key1 = _derive_fernet_key("clinic-pass-123")
    key2 = _derive_fernet_key("clinic-pass-123")
    key3 = _derive_fernet_key("different-pass")

    assert key1 == key2
    assert key1 != key3
    assert len(base64.urlsafe_b64decode(key1)) == 32


@pytest.mark.asyncio
async def test_create_and_verify_encrypted_backup():
    """Verify encrypted backup creation, checksum calculation, and manifest packing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        clinic_id = uuid4()
        db = MockAsyncDb()

        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)

            record = await BackupService.create_backup(
                db=db,  # type: ignore
                clinic_id=clinic_id,
                backup_type=BackupType.MANUAL,
                destination_type=BackupDestination.LOCAL,
                is_encrypted=True,
                password="strong-clinic-password",
                backup_dir=dest_dir,
            )

            assert record.clinic_id == clinic_id
            assert record.is_encrypted is True
            assert record.file_name.endswith(".dcb")

            backup_file = Path(record.file_path)
            assert backup_file.exists()

            # Verify recorded SHA-256 matches actual file on disk
            with open(backup_file, "rb") as f:
                content = f.read()
            assert hashlib.sha256(content).hexdigest() == record.checksum_sha256

            # Verify decryption with correct password
            fernet = Fernet(_derive_fernet_key("strong-clinic-password"))
            raw_zip = fernet.decrypt(content)
            assert len(raw_zip) > 0

            # Verify archive contents contain manifest and database.sql
            zip_tmp = dest_dir / "test_unpacked.zip"
            with open(zip_tmp, "wb") as f:
                f.write(raw_zip)

            with zipfile.ZipFile(zip_tmp, "r") as zf:
                namelist = zf.namelist()
                assert "manifest.json" in namelist
                assert "database.sql" in namelist
                manifest_data = json.loads(zf.read("manifest.json").decode())
                assert manifest_data["app"] == "DentalCare Pro"
                assert manifest_data["is_encrypted"] is True


@pytest.mark.asyncio
async def test_create_unencrypted_backup():
    """Verify unencrypted standard zip backup creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        db = MockAsyncDb()

        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)

            record = await BackupService.create_backup(
                db=db,  # type: ignore
                clinic_id=None,
                backup_type=BackupType.SCHEDULED,
                is_encrypted=False,
                backup_dir=dest_dir,
            )

            assert record.is_encrypted is False
            assert record.file_name.endswith(".zip")
            backup_file = Path(record.file_path)
            assert backup_file.exists()

            # Should be directly openable as zip
            with zipfile.ZipFile(backup_file, "r") as zf:
                assert "manifest.json" in zf.namelist()


@pytest.mark.asyncio
async def test_restore_backup_checksum_corruption_detection():
    """Verify corrupted backup file is caught before restoration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        backup_file = dest_dir / "corrupted.dcb"
        with open(backup_file, "wb") as f:
            f.write(b"tampered-content-not-matching-sha")

        record = BackupRecord(
            id=uuid4(),
            file_name="corrupted.dcb",
            file_path=str(backup_file),
            file_size_bytes=100,
            checksum_sha256="original-expected-sha256-hash",
            is_encrypted=True,
            status=BackupStatus.COMPLETED,
        )

        db = MockAsyncDb([record])

        with pytest.raises(ValueError, match="Integrity check failed: Checksum does not match"):
            await BackupService.restore_backup(
                db=db,  # type: ignore
                backup_id=record.id,
                password="pass",
            )


@pytest.mark.asyncio
async def test_restore_backup_wrong_password_detection():
    """Verify invalid password throws decryption error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        db = MockAsyncDb()

        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)

            record = await BackupService.create_backup(
                db=db,  # type: ignore
                is_encrypted=True,
                password="correct-password-123",
                backup_dir=dest_dir,
            )

            with pytest.raises(ValueError, match="Decryption failed"):
                await BackupService.restore_backup(
                    db=db,  # type: ignore
                    backup_id=record.id,
                    password="wrong-password-xyz",
                )


@pytest.mark.asyncio
async def test_restore_backup_successful_execution():
    """Verify successful decrypt and restore execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        db = MockAsyncDb()

        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = MagicMock(returncode=0)

            record = await BackupService.create_backup(
                db=db,  # type: ignore
                is_encrypted=True,
                password="valid-password",
                backup_dir=dest_dir,
            )

            res = await BackupService.restore_backup(
                db=db,  # type: ignore
                backup_id=record.id,
                password="valid-password",
            )

            assert res["success"] is True
            assert res["backup_id"] == str(record.id)
