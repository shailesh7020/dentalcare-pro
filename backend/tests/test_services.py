from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError

from app.api import health
from app.core.config import Settings
from app.dependencies.rate_limit import rate_limit
from app.services.storage import StorageHealthService


@pytest.mark.asyncio
async def test_local_storage_health_check() -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgresql+asyncpg://postgres:pass@localhost/db",
            "SECRET_KEY": "a" * 32,
            "JWT_SECRET": "b" * 32,
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
            "REFRESH_TOKEN_EXPIRE_DAYS": 14,
            "REDIS_URL": "redis://localhost:6379/0",
            "CORS_ORIGINS": "http://localhost:3000",
            "STORAGE_LOCAL_PATH": ".",
        }
    )
    assert await StorageHealthService(settings).check()


@pytest.mark.asyncio
async def test_rate_limit_fails_closed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings.model_validate(
        {
            "environment": "production",
            "DATABASE_URL": "postgresql+asyncpg://postgres:pass@localhost/db",
            "SECRET_KEY": "a" * 32,
            "JWT_SECRET": "b" * 32,
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
            "REFRESH_TOKEN_EXPIRE_DAYS": 14,
            "REDIS_URL": "redis://localhost:6379/0",
            "CORS_ORIGINS": "http://localhost:3000",
        }
    )
    monkeypatch.setattr("app.dependencies.rate_limit.get_settings", lambda: settings)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=SimpleNamespace(incr=raise_redis))),
        client=SimpleNamespace(host="127.0.0.1"),
    )
    with pytest.raises(HTTPException, match="unavailable"):
        await rate_limit("login", "login_rate_limit")(request)


async def raise_redis(_key: str) -> int:
    raise RedisConnectionError("offline")


class HealthyRedis:
    async def ping(self) -> bool:
        return True


class HealthyStorage:
    async def check(self) -> bool:
        return True


class HealthyConnection:
    async def execute(self, _query: object) -> None:
        return None


class HealthyEngine:
    @asynccontextmanager
    async def connect(self):
        yield HealthyConnection()


@pytest.mark.asyncio
async def test_readiness_reports_dependency_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health, "engine", HealthyEngine())
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis=HealthyRedis(), storage=HealthyStorage()))
    )
    response = await health.ready(request)
    assert response == {
        "status": "ok",
        "checks": {"database": True, "redis": True, "storage": True},
    }


@pytest.mark.asyncio
async def test_storage_rejects_unsupported_patient_upload() -> None:
    from io import BytesIO

    from fastapi import UploadFile

    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgresql+asyncpg://postgres:pass@localhost/db",
            "SECRET_KEY": "a" * 32,
            "JWT_SECRET": "b" * 32,
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
            "REFRESH_TOKEN_EXPIRE_DAYS": 14,
            "REDIS_URL": "redis://localhost:6379/0",
            "CORS_ORIGINS": "http://localhost:3000",
        }
    )
    upload = UploadFile(
        filename="script.exe",
        file=BytesIO(b"not a document"),
        headers={"content-type": "application/octet-stream"},
    )
    with pytest.raises(HTTPException, match="Only JPEG"):
        await StorageHealthService(settings).save_patient_upload(uuid4(), uuid4(), upload)
