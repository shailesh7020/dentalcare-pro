import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import bind_request_context, clear_request_context

logger = logging.getLogger("request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        bind_request_context(
            request_id=request_id,
            user_id=None,
            clinic_id=None,
            ip_address=request.client.host if request.client else None,
            endpoint=request.url.path,
        )
        started = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            if response is not None:
                response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
            logger.info(
                "request.completed status=%s duration_ms=%s",
                response.status_code if response else 500,
                elapsed_ms,
            )
            clear_request_context()
