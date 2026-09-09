from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

import jwt

from app.core.config import get_settings


def create_access_token(subject: str, clinic_id: str | None, role: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "clinic_id": clinic_id, "role": role, "exp": expires_at},
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token() -> tuple[str, str, datetime]:
    settings = get_settings()
    token = token_urlsafe(48)
    expiry = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return token, sha256(token.encode()).hexdigest(), expiry


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()
