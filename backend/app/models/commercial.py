from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDAuditMixin


class SignatureType(StrEnum):
    DRAWN = "DRAWN"
    UPLOADED = "UPLOADED"


class BackupType(StrEnum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    PRE_UPDATE = "PRE_UPDATE"


class BackupStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"


class BackupDestination(StrEnum):
    LOCAL = "LOCAL"
    EXTERNAL = "EXTERNAL"
    NETWORK = "NETWORK"
    S3 = "S3"


class ClinicianSignature(Base, UUIDAuditMixin):
    __tablename__ = "clinician_signatures"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    signature_data: Mapped[str] = mapped_column(Text, nullable=False)
    signature_type: Mapped[str] = mapped_column(String(32), default=SignatureType.DRAWN, nullable=False)
    verification_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BackupRecord(Base, UUIDAuditMixin):
    __tablename__ = "backup_records"

    clinic_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_type: Mapped[str] = mapped_column(String(32), default=BackupDestination.LOCAL, nullable=False)
    backup_type: Mapped[str] = mapped_column(String(32), default=BackupType.MANUAL, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=BackupStatus.COMPLETED, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
