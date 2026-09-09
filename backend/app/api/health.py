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
    description="Checks PostgreSQL, Redis, and configured storage.",
)
async def ready(request: Request):  # type: ignore[no-untyped-def]
    checks: dict[str, bool] = {"database": False, "redis": False, "storage": False}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = True
    except SQLAlchemyError as error:
        logger.warning("health.database_unavailable error=%s", type(error).__name__)
    try:
        await request.app.state.redis.ping()
        checks["redis"] = True
    except RedisError as error:
        logger.warning("health.redis_unavailable error=%s", type(error).__name__)
    checks["storage"] = await request.app.state.storage.check()
    if all(checks.values()):
        return {"status": "ok", "checks": checks}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "checks": checks},
    )
