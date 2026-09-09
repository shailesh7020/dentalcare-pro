# backend/app/middleware/remote_access.py
"""
DentalCare Pro - Hybrid Remote Access Middleware & Guardrails
Detects remote requests from Cloudflare Tunnel, Tailscale, or external gateways,
and strictly prohibits destructive deletions and database administration.
"""
from __future__ import annotations

import ipaddress
import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("dentalcare.remote_access")

# RFC 1918 and loopback private networks
PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Paths prohibited from destructive remote modifications
PROHIBITED_REMOTE_DELETE_PREFIXES = (
    "/api/v1/patients",
    "/api/v1/invoices",
    "/api/v1/billing",
    "/api/v1/treatments",
    "/api/v1/backups",
    "/api/v1/audit",
    "/api/v1/database",
    "/api/v1/admin/settings",
)

PROHIBITED_REMOTE_ADMIN_PATHS = (
    "/api/v1/backups/restore",
    "/api/v1/database/migrate",
    "/api/v1/database/reset",
)


def is_private_ip(ip_str: str) -> bool:
    """Check if an IP address belongs to local loopback or clinic LAN."""
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return any(ip in net for net in PRIVATE_NETWORKS)
    except ValueError:
        return False


class RemoteAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Detect if request is remote
        client_host = request.client.host if request.client else "127.0.0.1"
        cf_ip = request.headers.get("CF-Connecting-IP")
        tailscale_header = request.headers.get("X-Tailscale-Client")
        remote_header = request.headers.get("X-Remote-Access", "").lower() == "true"
        x_forwarded_for = request.headers.get("X-Forwarded-For")

        is_remote = False
        effective_ip = client_host

        if cf_ip:
            is_remote = True
            effective_ip = cf_ip.strip()
        elif tailscale_header:
            is_remote = True
            effective_ip = tailscale_header.strip()
        elif remote_header:
            is_remote = True
        elif x_forwarded_for:
            # Check the first IP in the chain
            first_ip = x_forwarded_for.split(",")[0].strip()
            if not is_private_ip(first_ip):
                is_remote = True
                effective_ip = first_ip
        elif not is_private_ip(client_host):
            is_remote = True
            effective_ip = client_host

        request.state.is_remote = is_remote
        request.state.remote_ip = effective_ip

        # 2. Guardrails: Prohibit destructive actions remotely
        path = request.url.path.rstrip("/")
        method = request.method.upper()

        if is_remote:
            # Block destructive database administration
            if path in PROHIBITED_REMOTE_ADMIN_PATHS:
                logger.warning(
                    "Remote destructive admin access blocked: ip=%s path=%s method=%s",
                    effective_ip,
                    path,
                    method,
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Prohibited remote action: Database restore and raw administration can only be performed on-premise at the clinic server.",
                        "code": "REMOTE_ADMIN_PROHIBITED",
                        "path": path,
                    },
                )

            # Block DELETE on clinical records, invoices, backups, audits
            if method == "DELETE" and any(path.startswith(prefix) for prefix in PROHIBITED_REMOTE_DELETE_PREFIXES):
                logger.warning(
                    "Remote delete operation blocked: ip=%s path=%s method=%s",
                    effective_ip,
                    path,
                    method,
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Prohibited remote action: Destructive deletions can only be performed on-premise on the clinic server.",
                        "code": "REMOTE_DELETION_PROHIBITED",
                        "path": path,
                    },
                )

        response = await call_next(request)
        response.headers["X-Remote-Access"] = "true" if is_remote else "false"
        response.headers["X-Clinic-Source"] = "on-premise-server"
        return response
