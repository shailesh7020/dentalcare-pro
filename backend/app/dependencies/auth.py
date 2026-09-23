from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import bind_request_context
from app.database.session import get_db
from app.models import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
    )
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[get_settings().jwt_algorithm],
        )
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as error:
        raise credentials_error from error
    user = await db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None or not user.is_active:
        raise credentials_error
    bind_request_context(
        user_id=str(user.id), clinic_id=str(user.clinic_id) if user.clinic_id else None
    )
    return user


async def current_user_flexible(
    token_header: str | None = Depends(oauth2_scheme_optional),
    token_query: str | None = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = token_header or token_query
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
    )
    if not token:
        raise credentials_error
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[get_settings().jwt_algorithm],
        )
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as error:
        raise credentials_error from error
    user = await db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None or not user.is_active:
        raise credentials_error
    bind_request_context(
        user_id=str(user.id), clinic_id=str(user.clinic_id) if user.clinic_id else None
    )
    return user


def require_roles(*roles: Role) -> Callable:
    async def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency


def require_roles_flexible(*roles: Role) -> Callable:
    async def dependency(user: User = Depends(current_user_flexible)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency

