from __future__ import annotations

import io
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException, UploadFile
import pytest

from app.models.mobile import MobileClinicalMedia
from app.services.clinical_storage_service import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    AntiVirusService,
    ClinicalStorageService,
)


def test_antivirus_heuristic_malicious_pe_header():
    """Verify that files with Windows PE/MZ header disguised as media are caught."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # MZ header (executable/DLL signature)
        f.write(b"MZ\x90\x00\x03\x00\x00\x00malicious-payload-code")
        file_path = Path(f.name)

    try:
        is_clean, details = AntiVirusService.scan_file(file_path)
        assert is_clean is False
        assert "Prohibited executable binary payload detected" in details
    finally:
        if file_path.exists():
            file_path.unlink()


def test_antivirus_heuristic_malicious_elf_header():
    """Verify that files with Linux ELF header disguised as media are caught."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # \x7fELF header
        f.write(b"\x7fELF\x02\x01\x01\x00malicious-linux-binary")
        file_path = Path(f.name)

    try:
        is_clean, details = AntiVirusService.scan_file(file_path)
        assert is_clean is False
        assert "Prohibited executable binary payload detected" in details
    finally:
        if file_path.exists():
            file_path.unlink()


def test_antivirus_clean_file():
    """Verify standard clean files pass heuristic check."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # PNG signature
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        file_path = Path(f.name)

    try:
        is_clean, details = AntiVirusService.scan_file(file_path)
        assert is_clean is True
        assert "Passed security verification" in details or "Windows Defender" in details
    finally:
        if file_path.exists():
            file_path.unlink()


@pytest.mark.asyncio
async def test_clinical_storage_unsupported_mime_type():
    """Verify upload rejection for unsupported MIME type (e.g. .exe / executable)."""
    upload = UploadFile(
        file=io.BytesIO(b"dummy"),
        filename="setup.exe",
        headers={"content-type": "application/x-msdownload"},
    )
    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await ClinicalStorageService.save_clinical_file(
            db=db,
            clinic_id=uuid4(),
            patient_id=uuid4(),
            captured_by_id=uuid4(),
            category="xray",
            upload=upload,
        )

    assert exc_info.value.status_code == 415
    assert "Unsupported file format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_clinical_storage_exceeds_max_size():
    """Verify upload rejection for files exceeding MAX_FILE_SIZE (50MB)."""
    # Create an upload exceeding MAX_FILE_SIZE
    large_content = b"0" * (MAX_FILE_SIZE + 1024)
    upload = UploadFile(
        file=io.BytesIO(large_content),
        filename="huge_scan.dcm",
        headers={"content-type": "application/dicom"},
    )
    db = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await ClinicalStorageService.save_clinical_file(
            db=db,
            clinic_id=uuid4(),
            patient_id=uuid4(),
            captured_by_id=uuid4(),
            category="xray",
            upload=upload,
        )

    assert exc_info.value.status_code == 413
    assert "File exceeds maximum allowed size" in exc_info.value.detail


@pytest.mark.asyncio
async def test_clinical_storage_successful_upload_and_path_sanitization():
    """Verify successful upload, path isolation by patient, and safe random UUID filename."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_base = Path(tmpdir)

        clean_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRclean-test-image"
        # Attempt path traversal in filename: ../../malicious.png
        upload = UploadFile(
            file=io.BytesIO(clean_png),
            filename="../../malicious.png",
            headers={"content-type": "image/png"},
        )

        clinic_id = uuid4()
        patient_id = uuid4()
        captured_by_id = uuid4()

        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with patch.object(ClinicalStorageService, "get_storage_base", return_value=storage_base):
            media = await ClinicalStorageService.save_clinical_file(
                db=db,
                clinic_id=clinic_id,
                patient_id=patient_id,
                captured_by_id=captured_by_id,
                category="photo",
                upload=upload,
                tooth_number=18,
                notes="Pre-op intraoral photograph",
            )

            assert media.patient_id == patient_id
            assert media.media_type == "PHOTO"
            assert media.tooth_number == 18
            assert "malicious" not in media.file_url
            assert ".." not in media.file_url

            # Verify file exists strictly in isolated directory
            expected_dir = storage_base / "photo" / str(clinic_id) / str(patient_id)
            assert expected_dir.exists()
            stored_files = list(expected_dir.glob("*.png"))
            assert len(stored_files) == 1
            assert stored_files[0].read_bytes() == clean_png
