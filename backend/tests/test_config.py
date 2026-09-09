import pytest
from pydantic import ValidationError

from app.core.config import Settings


def valid_settings() -> dict[str, object]:
    return {
        "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/dentalcare",
        "SECRET_KEY": "a" * 32,
        "JWT_SECRET": "b" * 32,
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
        "REFRESH_TOKEN_EXPIRE_DAYS": 14,
        "REDIS_URL": "redis://localhost:6379/0",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001",
    }


def build_settings(monkeypatch: pytest.MonkeyPatch, values: dict[str, object]) -> Settings:
    for name in (
        "ENVIRONMENT",
        "DATABASE_URL",
        "SECRET_KEY",
        "JWT_SECRET",
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "REDIS_URL",
        "CORS_ORIGINS",
    ):
        monkeypatch.delenv(name, raising=False)
    return Settings(_env_file=None, **values)


def test_settings_requires_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    values = valid_settings()
    values.pop("JWT_SECRET")
    with pytest.raises(ValidationError):
        build_settings(monkeypatch, values)


def test_settings_rejects_short_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    values = valid_settings()
    values["SECRET_KEY"] = "short"
    with pytest.raises(ValidationError, match="at least 32"):
        build_settings(monkeypatch, values)


def test_settings_parses_multiple_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    assert build_settings(monkeypatch, valid_settings()).cors_origin_list == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]


def test_production_rejects_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    values = valid_settings() | {"environment": "production", "CORS_ORIGINS": "*"}
    with pytest.raises(ValidationError, match="cannot contain"):
        build_settings(monkeypatch, values)
