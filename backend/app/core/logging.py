import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_context: ContextVar[dict[str, str | None] | None] = ContextVar(
    "request_context", default=None
)


def bind_request_context(**values: str | None) -> None:
    request_context.set({**(request_context.get() or {}), **values})


def clear_request_context() -> None:
    request_context.set({})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            **(request_context.get() or {}),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").handlers = [handler]


def security_logger() -> logging.Logger:
    return logging.getLogger("security")


def audit_logger() -> logging.Logger:
    return logging.getLogger("audit")
