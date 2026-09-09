from collections.abc import Callable

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.config import get_settings


def rate_limit(bucket: str, limit_name: str) -> Callable:
    async def dependency(request: Request) -> None:
        settings = get_settings()
        if settings.environment == "test":
            return
        limit = getattr(settings, limit_name)
        client = getattr(request.app.state, "redis", None)
        if client is None:
            if settings.environment == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiter unavailable",
                )
            return
        ip_address = request.client.host if request.client else "unknown"
        key = f"rate-limit:{bucket}:{ip_address}"
        try:
            count = await client.incr(key)
        except RedisError as error:
            if settings.environment == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiter unavailable",
                ) from error
            return
        if count == 1:
            await client.expire(key, settings.rate_limit_window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
            )

    return dependency
