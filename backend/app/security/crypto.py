import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = hashlib.sha256(settings.secret_key.get_secret_value().encode()).digest()
    url_safe_key = base64.urlsafe_b64encode(key)
    return Fernet(url_safe_key)


def encrypt_value(raw: str | None) -> str | None:
    if not raw:
        return None
    f = _get_fernet()
    return f.encrypt(raw.encode()).decode()


def decrypt_value(encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        # Fallback for unencrypted legacy values
        return encrypted
