from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


def error_response(
    request: Request, status_code: int, message: str, code: str, details: Any = None
) -> JSONResponse:
    error: dict[str, Any] = {"code": code}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        request,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Request validation failed",
        "VALIDATION_ERROR",
        exc.errors(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = {
        status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_ERROR",
        status.HTTP_403_FORBIDDEN: "AUTHORIZATION_ERROR",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    }.get(exc.status_code, "REQUEST_ERROR")
    return error_response(request, exc.status_code, str(exc.detail), code)


async def sqlalchemy_exception_handler(request: Request, _: SQLAlchemyError) -> JSONResponse:
    return error_response(
        request,
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Service temporarily unavailable",
        "DATABASE_ERROR",
    )


async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
    return error_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected error occurred",
        "INTERNAL_SERVER_ERROR",
    )
