import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.dependencies.rate_limit import rate_limit
from app.models import AuditEvent, RefreshToken, User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserRead
from app.security.passwords import verify_password
from app.security.tokens import create_access_token, create_refresh_token, token_digest

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger("security")

AUTH_ERROR_RESPONSES = {
    401: {"description": "Invalid credentials, expired token, or detected token replay."},
    429: {"description": "Configured request limit exceeded."},
}


async def issue_tokens(user: User, db: AsyncSession, family_id: UUID | None = None) -> TokenPair:
    refresh_token, refresh_hash, expires_at = create_refresh_token()
    token_record = RefreshToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
        family_id=family_id or UUID(int=0),
    )
    if family_id is None:
        token_record.family_id = token_record.id
    db.add(token_record)
    user.last_login_at = datetime.now(UTC)
    await db.flush()
    return TokenPair(
        access_token=create_access_token(
            str(user.id), str(user.clinic_id) if user.clinic_id else None, user.role.value
        ),
        refresh_token=refresh_token,
    )


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Create an authenticated session",
    description="Authenticates a staff member and returns a short-lived access token with a rotating refresh token.",
    responses=AUTH_ERROR_RESPONSES,
)
async def login(
    payload: LoginRequest,
    _: None = Depends(rate_limit("login", "login_rate_limit")),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    user = await db.scalar(
        select(User).where(User.email == payload.email, User.deleted_at.is_(None))
    )
    is_valid_pw = False
    if user and user.is_active:
        is_valid_pw = await asyncio.to_thread(verify_password, payload.password, user.password_hash)
    if not user or not user.is_active or not is_valid_pw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    db.add(
        AuditEvent(
            clinic_id=user.clinic_id,
            actor_id=user.id,
            action="LOGIN",
            entity_type="USER",
            entity_id=str(user.id),
        )
    )
    token_pair = await issue_tokens(user, db)
    await db.commit()
    return token_pair


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate a refresh token",
    description="Consumes a refresh token once. Reuse revokes its entire token family.",
    responses=AUTH_ERROR_RESPONSES,
)
async def refresh(
    payload: RefreshRequest,
    _: None = Depends(rate_limit("refresh", "refresh_rate_limit")),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    refresh = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_digest(payload.refresh_token),
        )
    )
    if refresh is None or refresh.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired"
        )
    if refresh.revoked_at is not None:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == refresh.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await db.commit()
        logger.warning("refresh_token.replay_detected user_id=%s", refresh.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token replay detected"
        )
    user = await db.get(User, refresh.user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unavailable")
    refresh.revoked_at = datetime.now(UTC)
    token_pair = await issue_tokens(user, db, refresh.family_id)
    replacement = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_digest(token_pair.refresh_token)
        )
    )
    refresh.replaced_by_token_id = replacement.id if replacement else None
    await db.commit()
    return token_pair


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
    description="Revokes the supplied refresh token so it cannot mint another session.",
)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> None:
    refresh = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_digest(payload.refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if refresh:
        refresh.revoked_at = datetime.now(UTC)
        db.add(
            AuditEvent(
                actor_id=refresh.user_id,
                action="LOGOUT",
                entity_type="USER",
                entity_id=str(refresh.user_id),
            )
        )
        await db.commit()


@router.get("/me", response_model=UserRead, summary="Get the authenticated staff profile")
async def me(user: User = Depends(current_user)) -> User:
    return user
