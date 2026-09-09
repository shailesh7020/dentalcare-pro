import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.config import get_settings

# In-memory sliding window fallback for local / offline clinic deployments
_in_memory_buckets: dict[str, list[float]] = {}


def _in_memory_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - window_seconds
    timestamps = _in_memory_buckets.setdefault(key, [])
    # Evict expired timestamps
    _in_memory_buckets[key] = [t for t in timestamps if t > cutoff]
    if len(_in_memory_buckets[key]) >= limit:
        return False
    _in_memory_buckets[key].append(now)
    return True


def rate_limit(bucket: str, limit_name: str) -> Callable:
    async def dependency(request: Request) -> None:
        settings = get_settings()
        if settings.environment == "test":
            return
        limit = getattr(settings, limit_name)
        ip_address = request.client.host if request.client else "unknown"
        key = f"rate-limit:{bucket}:{ip_address}"

        client = getattr(request.app.state, "redis", None)
        if client is None:
            if settings.environment == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiter unavailable",
                )
            # Fallback to in-memory sliding window rate limiting
            allowed = _in_memory_rate_limit(key, limit, settings.rate_limit_window_seconds)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
                )
            return

        try:
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, settings.rate_limit_window_seconds)
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
                )
        except RedisError as error:
            if settings.environment == "production":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiter unavailable",
                ) from error
            # Graceful degradation to in-memory limiter in non-production mode
            allowed = _in_memory_rate_limit(key, limit, settings.rate_limit_window_seconds)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
                )
            return

    return dependency
