from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDAuditMixin


class Role(StrEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    REGIONAL_MANAGER = "REGIONAL_MANAGER"
    BRANCH_MANAGER = "BRANCH_MANAGER"
    CLINIC_ADMIN = "CLINIC_ADMIN"
    DENTIST = "DENTIST"
    HYGIENIST = "HYGIENIST"
    RECEPTIONIST = "RECEPTIONIST"
    ASSISTANT = "ASSISTANT"
    ACCOUNTANT = "ACCOUNTANT"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    HR_MANAGER = "HR_MANAGER"
    PATIENT = "PATIENT"


class Clinic(Base, UUIDAuditMixin):
    __tablename__ = "clinics"
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True, nullable=True
    )
    region_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    branch_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    tax_configuration: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_main_branch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class User(Base, UUIDAuditMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "clinic_id IS NOT NULL OR organization_id IS NOT NULL OR role IN ('SUPER_ADMIN', 'ORGANIZATION_ADMIN')",
            name="ck_users_clinic_assignment",
        ),
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True, nullable=True
    )
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Base, UUIDAuditMixin):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    family_id: Mapped[UUID] = mapped_column(default=uuid4, index=True, nullable=False)
    replaced_by_token_id: Mapped[UUID | None] = mapped_column(ForeignKey("refresh_tokens.id"))


class AuditEvent(Base, UUIDAuditMixin):
    __tablename__ = "audit_events"
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[str | None] = mapped_column(Text)
