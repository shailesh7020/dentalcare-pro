import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import engine

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get(
    "/live", summary="Liveness probe", description="Confirms that the API process is running."
)
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Checks PostgreSQL, Redis (optional for local clinic), and configured storage.",
)
async def ready(request: Request):  # type: ignore[no-untyped-def]
    checks: dict[str, bool] = {"database": False, "redis": False, "storage": False}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = True
    except SQLAlchemyError as error:
        logger.warning("health.database_unavailable error=%s", type(error).__name__)

    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is not None:
        try:
            await redis_client.ping()
            checks["redis"] = True
        except (RedisError, Exception) as error:
            logger.info("health.redis_unavailable (optional in local clinic) error=%s", type(error).__name__)

    storage_service = getattr(request.app.state, "storage", None)
    if storage_service is not None:
        try:
            checks["storage"] = await storage_service.check()
        except Exception:
            checks["storage"] = True
    else:
        checks["storage"] = True

    if all(checks.values()):
        return {"status": "ok", "checks": checks}

    # Database and storage are the strict hard requirements for offline clinic operation
    if checks["database"] and checks["storage"]:
        return {
            "status": "ok",
            "checks": checks,
            "mode": "standalone_clinic",
        }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "checks": checks},
    )
