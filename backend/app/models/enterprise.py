from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship

from app.models.base import Base, UUIDAuditMixin


class PatientSharingMode(StrEnum):
    SHARED = "SHARED"
    ISOLATED = "ISOLATED"
    TRANSFER_ONLY = "TRANSFER_ONLY"


class TransferStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InventoryTransferStatus(StrEnum):
    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class AnnouncementType(StrEnum):
    BROADCAST = "BROADCAST"
    REGIONAL = "REGIONAL"
    BRANCH_ALERT = "BRANCH_ALERT"
    EMERGENCY = "EMERGENCY"


class AnnouncementScope(StrEnum):
    ALL = "ALL"
    REGION = "REGION"
    BRANCH = "BRANCH"
    ROLE = "ROLE"


class Organization(Base, UUIDAuditMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(40), default="ENTERPRISE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    theme_color: Mapped[str] = mapped_column(String(40), default="#0d9488", nullable=False)
    primary_email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_sharing_mode: Mapped[PatientSharingMode] = mapped_column(
        Enum(PatientSharingMode, name="patient_sharing_mode"),
        default=PatientSharingMode.SHARED,
        nullable=False,
    )
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    regions: Mapped[list[Region]] = orm_relationship("Region", back_populates="organization", cascade="all, delete-orphan")


class Region(Base, UUIDAuditMixin):
    __tablename__ = "regions"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    regional_manager_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped[Organization] = orm_relationship("Organization", back_populates="regions")


class Department(Base, UUIDAuditMixin):
    __tablename__ = "departments"

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    head_dentist_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EnterpriseRole(Base, UUIDAuditMixin):
    __tablename__ = "enterprise_roles"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=True
    )
    role_key: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EnterprisePermission(Base, UUIDAuditMixin):
    __tablename__ = "enterprise_permissions"

    permission_key: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    module: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RolePermissionMapping(Base):
    __tablename__ = "role_permission_mappings"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("enterprise_roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("enterprise_permissions.id", ondelete="CASCADE"), primary_key=True
    )


class UserBranchAssignment(Base, UUIDAuditMixin):
    __tablename__ = "user_branch_assignments"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_override: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    working_days_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserPermissionOverride(Base):
    __tablename__ = "user_permission_overrides"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("enterprise_permissions.id", ondelete="CASCADE"), primary_key=True
    )
    is_granted: Mapped[bool] = mapped_column(Boolean, nullable=False)


class PatientTransfer(Base, UUIDAuditMixin):
    __tablename__ = "patient_transfers"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    to_clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    initiated_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, name="patient_transfer_status"),
        default=TransferStatus.PENDING,
        nullable=False,
    )
    transfer_reason: Mapped[str] = mapped_column(Text, nullable=False)
    records_included_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PatientMergeRecord(Base, UUIDAuditMixin):
    __tablename__ = "patient_merge_records"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    primary_patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    duplicate_patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    merged_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    merge_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    merged_data_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class InventoryTransfer(Base, UUIDAuditMixin):
    __tablename__ = "inventory_transfers"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transfer_number: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    from_clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    to_clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    item_id: Mapped[UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[InventoryTransferStatus] = mapped_column(
        Enum(InventoryTransferStatus, name="inventory_transfer_status"),
        default=InventoryTransferStatus.DRAFT,
        nullable=False,
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class EnterpriseAnnouncement(Base, UUIDAuditMixin):
    __tablename__ = "enterprise_announcements"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    announcement_type: Mapped[AnnouncementType] = mapped_column(
        Enum(AnnouncementType, name="announcement_type"),
        default=AnnouncementType.BROADCAST,
        nullable=False,
    )
    target_scope: Mapped[AnnouncementScope] = mapped_column(
        Enum(AnnouncementScope, name="announcement_scope"),
        default=AnnouncementScope.ALL,
        nullable=False,
    )
    target_id: Mapped[UUID | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EnterpriseAuditLog(Base, UUIDAuditMixin):
    __tablename__ = "enterprise_audit_logs"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), index=True, nullable=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
