# backend/app/api/v1/remote.py
"""
DentalCare Pro - Hybrid Remote Access Router
Handles remote policy, two-factor authentication, remote device sessions,
and Cloudflare/Tailscale configuration.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user, require_roles
from app.models.identity import Role, User
from app.models.remote import TwoFactorSecret
from app.security.passwords import verify_password
from app.security.totp import TOTPService
from app.services.remote_access_service import RemoteAccessService

router = APIRouter(prefix="/remote", tags=["Hybrid Remote Access & 2FA"])

ADMIN_ROLES = (Role.SUPER_ADMIN, Role.CLINIC_ADMIN)


# Schemas
class RemoteConfigUpdate(BaseModel):
    is_remote_enabled: bool = True
    allowed_roles: list[str] = Field(
        default=["SUPER_ADMIN", "CLINIC_ADMIN", "DENTIST", "RECEPTIONIST"]
    )
    require_2fa: bool = False
    session_timeout_minutes: int = Field(default=480, ge=15, le=1440)
    tunnel_provider: str = Field(default="cloudflare")
    tunnel_hostname: str | None = None


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFactorDisableRequest(BaseModel):
    current_password: str = Field(..., min_length=1)


@router.get("/status")
async def get_remote_status(
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check current remote access status, connection origin, and user permissions."""
    if not user.clinic_id and user.role != Role.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="User is not assigned to a clinic.")

    clinic_id = user.clinic_id or user.id
    config = await RemoteAccessService.get_or_create_config(clinic_id=clinic_id, db=db)
    allowed_roles = json.loads(config.allowed_roles_json)

    # Check user 2FA status
    tf_res = await db.execute(
        select(TwoFactorSecret).where(TwoFactorSecret.user_id == user.id)
    )
    tf_secret = tf_res.scalar_one_or_none()
    is_2fa_enabled = tf_secret.is_enabled if tf_secret else False

    is_remote = getattr(request.state, "is_remote", False)
    remote_ip = getattr(request.state, "remote_ip", request.client.host if request.client else "unknown")

    return {
        "is_remote_request": is_remote,
        "effective_ip": remote_ip,
        "clinic_id": str(clinic_id),
        "is_remote_enabled": config.is_remote_enabled,
        "require_2fa": config.require_2fa,
        "user_2fa_enabled": is_2fa_enabled,
        "user_role": user.role.value,
        "user_permitted_for_remote": user.role.value in allowed_roles,
        "tunnel_provider": config.tunnel_provider,
        "tunnel_hostname": config.tunnel_hostname,
        "session_timeout_minutes": config.session_timeout_minutes,
    }


@router.post("/config")
async def update_remote_config(
    body: RemoteConfigUpdate,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Configure clinic remote access policy (Admin only)."""
    if not user.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")

    config = await RemoteAccessService.get_or_create_config(clinic_id=user.clinic_id, db=db)
    config.is_remote_enabled = body.is_remote_enabled
    config.allowed_roles_json = json.dumps(body.allowed_roles)
    config.require_2fa = body.require_2fa
    config.session_timeout_minutes = body.session_timeout_minutes
    config.tunnel_provider = body.tunnel_provider
    config.tunnel_hostname = body.tunnel_hostname

    await db.commit()
    await db.refresh(config)
    return {"status": "updated", "message": "Clinic remote configuration updated."}


@router.post("/2fa/setup")
async def setup_two_factor(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a new TOTP base32 secret and provisioning URI."""
    tf_res = await db.execute(
        select(TwoFactorSecret).where(TwoFactorSecret.user_id == user.id)
    )
    tf_secret = tf_res.scalar_one_or_none()

    secret = TOTPService.generate_secret()
    backup_codes = TOTPService.generate_backup_codes(count=8)

    if not tf_secret:
        tf_secret = TwoFactorSecret(
            user_id=user.id,
            secret_base32=secret,
            is_enabled=False,
            backup_codes_json=json.dumps(backup_codes),
        )
        db.add(tf_secret)
    else:
        tf_secret.secret_base32 = secret
        tf_secret.is_enabled = False
        tf_secret.backup_codes_json = json.dumps(backup_codes)

    await db.commit()

    otp_uri = TOTPService.get_provisioning_uri(
        secret=secret,
        account_name=user.email,
        issuer="DentalCare Pro",
    )

    return {
        "secret": secret,
        "otpauth_uri": otp_uri,
        "backup_codes": backup_codes,
        "message": "Scan the OTP URI or enter the secret in your authenticator app, then verify with a 6-digit code.",
    }


@router.post("/2fa/verify")
async def verify_and_enable_two_factor(
    body: TwoFactorVerifyRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Verify 6-digit code and officially activate 2FA for the user."""
    tf_res = await db.execute(
        select(TwoFactorSecret).where(TwoFactorSecret.user_id == user.id)
    )
    tf_secret = tf_res.scalar_one_or_none()
    if not tf_secret:
        raise HTTPException(
            status_code=400, detail="2FA setup not initialized. Call /remote/2fa/setup first."
        )

    is_valid = TOTPService.verify_totp_code(secret=tf_secret.secret_base32, code=body.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid TOTP code. Please check your authenticator clock.")

    tf_secret.is_enabled = True
    await db.commit()
    return {"status": "verified", "is_enabled": True, "message": "Two-factor authentication successfully activated."}


@router.post("/2fa/disable")
async def disable_two_factor(
    body: TwoFactorDisableRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Disable 2FA after password re-authentication."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password verification.")

    tf_res = await db.execute(
        select(TwoFactorSecret).where(TwoFactorSecret.user_id == user.id)
    )
    tf_secret = tf_res.scalar_one_or_none()
    if tf_secret:
        tf_secret.is_enabled = False
        await db.commit()

    return {"status": "disabled", "is_enabled": False, "message": "Two-factor authentication disabled."}


@router.get("/sessions")
async def list_remote_sessions(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List active remote sessions for the current user."""
    return await RemoteAccessService.list_remote_sessions(user_id=user.id, db=db)


@router.delete("/sessions/{session_id}")
async def revoke_remote_session(
    session_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke a remote session."""
    revoked = await RemoteAccessService.revoke_session(
        session_id=session_id, user_id=user.id, db=db
    )
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "revoked", "message": "Remote session successfully terminated."}


@router.get("/tunnel/cloudflare-config")
async def get_cloudflare_tunnel_config(
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
    tunnel_id: str = Query(default="clinic-tunnel-uuid"),
    hostname: str = Query(default="clinic.dentalcarepro.local"),
) -> dict[str, str]:
    """Generate configuration file content for Cloudflare Tunnel on Windows."""
    yaml_config = RemoteAccessService.generate_cloudflare_config(
        tunnel_id=tunnel_id,
        credentials_file=f"C:\\ProgramData\\cloudflared\\{tunnel_id}.json",
        hostname=hostname,
    )
    return {"tunnel_id": tunnel_id, "config_yaml": yaml_config}
