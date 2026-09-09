# backend/app/models/remote.py
"""
DentalCare Pro - Hybrid Remote Access Models
Supports Cloudflare Tunnel / Tailscale zero-trust remote sessions,
two-factor authentication (TOTP), and clinic-level remote security policy.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin


class ClinicRemoteConfig(Base, UUIDAuditMixin):
    __tablename__ = "clinic_remote_configs"
    __table_args__ = (
        UniqueConstraint("clinic_id", name="uq_clinic_remote_config_clinic"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_remote_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_roles_json: Mapped[str] = mapped_column(
        Text,
        default='["SUPER_ADMIN", "CLINIC_ADMIN", "DENTIST", "RECEPTIONIST"]',
        nullable=False,
    )
    require_2fa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=480, nullable=False)  # 8 hrs
    tunnel_provider: Mapped[str] = mapped_column(String(40), default="cloudflare", nullable=False)
    tunnel_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    clinic = relationship("Clinic")


class TwoFactorSecret(Base, UUIDAuditMixin):
    __tablename__ = "two_factor_secrets"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_two_factor_secret_user"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    secret_base32: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")


class RemoteSession(Base, UUIDAuditMixin):
    __tablename__ = "remote_sessions"
    __table_args__ = (
        Index("ix_remote_sessions_user", "user_id"),
        Index("ix_remote_sessions_token_hash", "session_token_hash"),
        Index("ix_remote_sessions_expires", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True
    )
    session_token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(120), nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), default="MOBILE", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_2fa_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    clinic = relationship("Clinic")
