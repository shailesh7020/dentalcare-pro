from app.database.session import async_database_url
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, token_digest


def test_password_round_trip() -> None:
    password = "VerySecurePassword!2026"
    assert verify_password(password, hash_password(password))


def test_refresh_token_is_hashed() -> None:
    token, digest, _ = create_refresh_token()
    assert digest == token_digest(token)
    assert token != digest


def test_access_token_is_created() -> None:
    assert create_access_token("user-id", "clinic-id", "DENTIST")


def test_plain_postgres_url_uses_async_driver() -> None:
    assert async_database_url("postgresql://user:pass@localhost/database").startswith(
        "postgresql+asyncpg://"
    )
